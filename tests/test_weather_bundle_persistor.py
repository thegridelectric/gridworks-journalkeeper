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

from gjk.sema import SemaCodec
from gjk.sema.enums import GwChannelKind
from gjk.sema.types import GwWeatherForecastBundleGt
from gjk.weather_bundle_persistor import WeatherBundlePersistor, flat_channel_name

SAMPLES = Path(__file__).resolve().parents[1] / "src" / "gjk" / "sema" / "samples"
WEATHER_GNODE = "d1.weather"


def _sample_bundle() -> GwWeatherForecastBundleGt:
    payload = json.loads(
        (SAMPLES / "gw.weather.forecast.bundle.gt.002.json").read_text()
    )
    bundle = SemaCodec().from_dict(payload)
    assert isinstance(bundle, GwWeatherForecastBundleGt)
    return bundle


def test_message_id_is_the_bundles_own_uuid() -> None:
    from datetime import UTC, datetime

    p = WeatherBundlePersistor(logging.getLogger("test_weather_bundle"))
    bundle = _sample_bundle()
    t = datetime.fromtimestamp(1786550460, tz=UTC)
    info = p.persist_v002(WEATHER_GNODE, t, bundle)
    # Records are durable identities: replayed broadcast → same id.
    assert info.id == bundle.id
    assert info.created_at is None
    assert info.additional_db_operations is not None


def test_flat_channel_name_is_dash_rendering() -> None:
    assert flat_channel_name("kmlt.temperature") == "kmlt-temperature"


def test_bundle_creates_observation_channels_once(timescale_db_url: str) -> None:
    from datetime import UTC, datetime

    engine = create_engine(timescale_db_url)
    factory = sessionmaker(bind=engine, class_=Session)
    p = WeatherBundlePersistor(logging.getLogger("test_weather_bundle"))
    bundle = _sample_bundle()
    t = datetime.fromtimestamp(1786550460, tz=UTC)

    try:
        for _ in range(2):  # create-if-absent: a re-run adds nothing
            info = p.persist_v002(WEATHER_GNODE, t, bundle)
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
            observed = [b.observation_channel for b in bundle.binding_list]
            assert set(by_name) == {flat_channel_name(c.name) for c in observed}
            first = observed[0]
            row = by_name[flat_channel_name(first.name)]
            # OBSERVATION channels only, on the record's own facts, scoped
            # to the weather GNode (the fleet-scoped series has no TA).
            assert row.unit == first.unit
            assert row.display_name == first.display_name
            assert row.channel_type == GwChannelKind.WeatherObserved.value
            assert str(row.channel_id) == first.id
    finally:
        with factory() as db:
            db.query(ReadingChannelSql).filter(
                ReadingChannelSql.terminal_asset_alias == WEATHER_GNODE
            ).delete()
            db.commit()
        engine.dispose()
