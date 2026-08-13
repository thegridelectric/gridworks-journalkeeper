"""The bundle-creation → observed-series pseudo-channel mechanism.

Hermetic half: the natural message id and the channel derivation,
against the REAL snapshot sample (no mocks — the derivation rules are
the contract under test). DB half: create-if-absent idempotency
against the migrated harness DB.
"""

import json
import logging
from pathlib import Path

from gw_data.db.models import ReadingChannelSql
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from gjk.pseudo_channels import PseudoChannel
from gjk.sema import SemaCodec
from gjk.sema.types import GwWeatherForecastBundleGt
from gjk.weather_bundle_persistor import WeatherBundlePersistor, flat_channel_name

SAMPLES = Path(__file__).resolve().parents[1] / "src" / "gjk" / "sema" / "samples"
WEATHER_GNODE = "d1.weather"


def _sample_bundle() -> GwWeatherForecastBundleGt:
    payload = json.loads(
        (SAMPLES / "gw.weather.forecast.bundle.gt.000.json").read_text()
    )
    bundle = SemaCodec().from_dict(payload)
    assert isinstance(bundle, GwWeatherForecastBundleGt)
    return bundle


def test_message_id_is_the_bundles_own_uuid() -> None:
    from datetime import UTC, datetime

    p = WeatherBundlePersistor(logging.getLogger("test_weather_bundle"))
    bundle = _sample_bundle()
    t = datetime.fromtimestamp(1786550460, tz=UTC)
    info = p.persist_v000(WEATHER_GNODE, t, bundle)
    # Records are durable identities: replayed broadcast → same id.
    assert info.id == bundle.id
    assert info.created_at is None
    assert info.additional_db_operations is not None


def test_flat_channel_name_is_dash_rendering() -> None:
    assert (
        flat_channel_name("us.me.millinocket.temperature")
        == "us-me-millinocket-temperature"
    )


def test_bundle_creates_observation_channels_once(timescale_db_url: str) -> None:
    from datetime import UTC, datetime

    engine = create_engine(timescale_db_url)
    factory = sessionmaker(bind=engine, class_=Session)
    p = WeatherBundlePersistor(logging.getLogger("test_weather_bundle"))
    bundle = _sample_bundle()
    t = datetime.fromtimestamp(1786550460, tz=UTC)

    try:
        for _ in range(2):  # create-if-absent: a re-run adds nothing
            info = p.persist_v000(WEATHER_GNODE, t, bundle)
            with factory() as db:
                info.additional_db_operations(db)
                db.commit()

        with factory() as db:
            rows = (
                db
                .query(ReadingChannelSql)
                .filter(
                    ReadingChannelSql.terminal_asset_alias == WEATHER_GNODE,
                    ReadingChannelSql.deactivated_date.is_(None),
                )
                .all()
            )
            by_name = {r.name: r for r in rows}
            expected = {
                flat_channel_name(bundle.temp_observation_channel.name),
                flat_channel_name(bundle.wind_speed_observation_channel.name),
            }
            assert set(by_name) == expected
            temp = by_name[flat_channel_name(bundle.temp_observation_channel.name)]
            # OBSERVATION channels only, on the record's own facts, scoped
            # to the weather GNode (the fleet-scoped series has no TA).
            assert temp.unit == bundle.temp_observation_channel.unit
            assert temp.display_name == bundle.temp_observation_channel.display_name
            assert temp.channel_type == PseudoChannel.CHANNEL_TYPE
    finally:
        with factory() as db:
            db.query(ReadingChannelSql).filter(
                ReadingChannelSql.terminal_asset_alias == WEATHER_GNODE
            ).delete()
            db.commit()
        engine.dispose()
