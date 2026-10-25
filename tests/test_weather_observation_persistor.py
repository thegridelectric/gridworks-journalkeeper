"""Observed weather readings: a gw.weather.observation's values reach the
readings table on the rows the bundle made, at ObservationTime, through
the journaled channel records; an interpolated observation writes none.
Against the migrated harness DB, with the real snapshot samples."""

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from gw_data.db.models import MessageSql, ReadingChannelSql, ReadingSql
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from gjk.sema import SemaCodec
from gjk.sema.types import GwWeatherForecastBundleGt, GwWeatherObservation
from gjk.weather_bundle_persistor import WeatherBundlePersistor
from gjk.weather_observation_persistor import WeatherObservationPersistor

SAMPLES = Path(__file__).resolve().parents[1] / "src" / "gjk" / "sema" / "samples"
WEATHER_GNODE = "d1.weather"
RECEIVED = datetime.fromtimestamp(1786550460, tz=UTC)


def sample(name: str):
    return SemaCodec().from_dict(json.loads((SAMPLES / name).read_text()))


def test_observation_readings_reach_the_bundles_rows(timescale_db_url: str) -> None:
    engine = create_engine(timescale_db_url)
    factory = sessionmaker(bind=engine, class_=Session)
    log = logging.getLogger("test_weather_observation")
    bundle = sample("gw.weather.forecast.bundle.gt.002.json")
    assert isinstance(bundle, GwWeatherForecastBundleGt)
    observation = sample("gw.weather.observation.001.json")
    assert isinstance(observation, GwWeatherObservation)
    records = [b.observation_channel for b in bundle.binding_list]
    record_ids = {uuid.UUID(r.id) for r in records}
    try:
        with factory() as db:
            # The records as the journal holds them, then the rows the bundle makes.
            for record in records:
                db.add(
                    MessageSql(
                        id=uuid.UUID(record.id),
                        timestamp=RECEIVED,
                        created_at=None,
                        persisted_at=RECEIVED,
                        from_alias=WEATHER_GNODE,
                        message_type_name=record.type_name,
                        payload=record.to_dict(),
                    )
                )
            WeatherBundlePersistor(log).persist_v002(
                WEATHER_GNODE, RECEIVED, bundle
            ).additional_db_operations(db)
            db.commit()

        persistor = WeatherObservationPersistor(log)
        for _ in range(2):  # a replay adds nothing
            info = persistor.persist_v001(WEATHER_GNODE, RECEIVED, observation)
            with factory() as db:
                info.additional_db_operations(db)
                db.commit()

        with factory() as db:
            rows = {
                r.channel_id: r
                for r in db
                .query(ReadingChannelSql)
                .filter(ReadingChannelSql.channel_id.in_(record_ids))
                .all()
            }
            by_name = {r.name: r for r in records}
            readings = (
                db
                .query(ReadingSql)
                .filter(ReadingSql.channel_id.in_([r.id for r in rows.values()]))
                .all()
            )
            got = {
                (readings_row.channel_id, readings_row.timestamp, readings_row.value)
                for readings_row in readings
            }
            at = datetime.fromisoformat(observation.observation_time)
            expected = {
                (rows[uuid.UUID(by_name[rd.channel_name].id)].id, at, rd.value)
                for rd in observation.reading_list
            }
            assert got == expected
            assert len(readings) == len(observation.reading_list)

        interpolated = SemaCodec().from_dict({
            **observation.to_dict(),
            "Interpolated": True,
        })
        assert isinstance(interpolated, GwWeatherObservation)
        info = persistor.persist_v001(WEATHER_GNODE, RECEIVED, interpolated)
        with factory() as db:
            info.additional_db_operations(db)
            db.commit()
            assert db.query(ReadingSql).filter(
                ReadingSql.channel_id.in_([r.id for r in rows.values()])
            ).count() == len(observation.reading_list)
    finally:
        with factory() as db:
            row_ids = [
                r.id
                for r in db
                .query(ReadingChannelSql)
                .filter(ReadingChannelSql.terminal_asset_alias == WEATHER_GNODE)
                .all()
            ]
            db.query(ReadingSql).filter(ReadingSql.channel_id.in_(row_ids)).delete()
            db.query(ReadingChannelSql).filter(
                ReadingChannelSql.terminal_asset_alias == WEATHER_GNODE
            ).delete()
            db.query(MessageSql).filter(MessageSql.id.in_(record_ids)).delete()
            db.commit()
        engine.dispose()
