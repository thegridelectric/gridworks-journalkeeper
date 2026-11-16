"""A gw.weather.channel.gt broadcast alone gives the observed series its
reading channel, so a station in no bundle (an archive replay's) has
rows for its observations to land on; the bundle ensuring the same
channel adds nothing. Against the migrated harness DB, with the real
snapshot samples."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from gw_data.db.models import ReadingChannelSql
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from gjk.sema import SemaCodec
from gjk.sema.enums import GwChannelKind
from gjk.sema.types import GwWeatherChannelGt, GwWeatherForecastBundleGt
from gjk.weather_bundle_persistor import WeatherBundlePersistor
from gjk.weather_channel_persistor import WeatherChannelPersistor, flat_channel_name

SAMPLES = Path(__file__).resolve().parents[1] / "src" / "gjk" / "sema" / "samples"
WEATHER_GNODE = "d1.weather"
RECEIVED = datetime.fromtimestamp(1786550460, tz=UTC)


def sample(name: str):
    return SemaCodec().from_dict(json.loads((SAMPLES / name).read_text()))


def test_message_id_is_the_records_own_uuid() -> None:
    record = sample("gw.weather.channel.gt.002.json")
    assert isinstance(record, GwWeatherChannelGt)
    info = WeatherChannelPersistor(logging.getLogger("test")).persist_v002(
        WEATHER_GNODE, RECEIVED, record
    )
    assert info.id == record.id
    assert info.created_at is None
    assert info.additional_db_operations is not None


def test_channel_record_alone_creates_its_row_once(timescale_db_url: str) -> None:
    engine = create_engine(timescale_db_url)
    factory = sessionmaker(bind=engine, class_=Session)
    log = logging.getLogger("test_weather_channel")
    bundle = sample("gw.weather.forecast.bundle.gt.002.json")
    assert isinstance(bundle, GwWeatherForecastBundleGt)
    # One of the bundle's own channels, broadcast on its own first.
    record = bundle.binding_list[0].observation_channel

    def active_rows(db: Session) -> list[ReadingChannelSql]:
        return (
            db
            .query(ReadingChannelSql)
            .filter(
                ReadingChannelSql.terminal_asset_alias == WEATHER_GNODE,
                ReadingChannelSql.deactivated_date.is_(None),
            )
            .all()
        )

    try:
        for _ in range(2):  # create-if-absent: a re-run adds nothing
            info = WeatherChannelPersistor(log).persist_v002(
                WEATHER_GNODE, RECEIVED, record
            )
            with factory() as db:
                info.additional_db_operations(db)
                db.commit()
        with factory() as db:
            rows = active_rows(db)
            assert [r.name for r in rows] == [flat_channel_name(record.name)]
            row = rows[0]
            assert str(row.channel_id) == record.id
            assert row.unit == record.unit
            assert row.display_name == record.display_name
            assert row.channel_type == GwChannelKind.WeatherObserved.value
            first_id = row.id

        # The bundle that binds this channel ensures the same row and
        # creates only the channels the record broadcast has not.
        info = WeatherBundlePersistor(log).persist_v002(WEATHER_GNODE, RECEIVED, bundle)
        with factory() as db:
            info.additional_db_operations(db)
            db.commit()
        with factory() as db:
            by_name = {r.name: r for r in active_rows(db)}
            assert set(by_name) == {
                flat_channel_name(b.observation_channel.name)
                for b in bundle.binding_list
            }
            assert by_name[flat_channel_name(record.name)].id == first_id
    finally:
        with factory() as db:
            db.query(ReadingChannelSql).filter(
                ReadingChannelSql.terminal_asset_alias == WEATHER_GNODE
            ).delete()
            db.commit()
        engine.dispose()
