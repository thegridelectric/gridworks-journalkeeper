"""The weather service sends its bundles in one slot, from one alias at one
MessageCreatedMs, so a gw.weather.forecast row's id tells the bundles apart:
at 002 it is the ForecastUid, at 001 a uuid5 that includes the bundle name.
Either way the id is independent of the receipt time, so the rabbit and S3
paths dedupe on the (timestamp, id) key."""

import logging
from datetime import UTC, datetime, timedelta

from gjk.gw_weather_forecast_persistor import GwWeatherForecastPersistor
from gjk.sema import SemaCodec
from gjk.sema.types import GwWeatherForecast
from gjk.sema.types.old_versions.gw_weather_forecast_001 import GwWeatherForecast001
from gjk.sema_message_persistor import SemaMessagePersistor

FROM_ALIAS = "hw1.isone.weather"
CREATED_MS = 1792094460033
CREATED_AT = datetime.fromtimestamp(CREATED_MS / 1000, tz=UTC)
UIDS = {
    "us.me.millinocket.bobcat": "5f1c2b3a-8d4e-4f60-9a7b-1c2d3e4f5a6b",
    "us.me.millinocket.raccoon": "0b7d4c2e-6a1f-4c3d-8e9f-2a3b4c5d6e7f",
    "us.me.millinocket.moose": "9c8b7a6d-5e4f-4a3b-9c2d-1e0f9a8b7c6d",
}
SERIES = [
    {
        "ChannelName": "kmlt.temperature.forecast.nws.hourly",
        "Quantity": "Temperature",
        "Values": [512, 498],
        "Fidelity": "Live",
        "SourceUpdatedTime": "2026-10-15T20:01:57Z",
        "TypeName": "gw.weather.forecast.series",
        "Version": "000",
    }
]


def forecast_002(bundle: str) -> GwWeatherForecast:
    return SemaCodec().from_dict(
        {
            "ForecastUid": UIDS[bundle],
            "BundleName": bundle,
            "MessageCreatedMs": CREATED_MS,
            "FirstSliceStart": "2026-10-15T21:00:00Z",
            "SeriesList": SERIES,
            "TypeName": "gw.weather.forecast",
            "Version": "002",
        },
        expect=GwWeatherForecast,
    )


def forecast_001(bundle: str) -> GwWeatherForecast001:
    return SemaCodec().from_dict(
        {
            "BundleName": bundle,
            "MessageCreatedMs": CREATED_MS,
            "FirstSliceStart": "2026-10-15T21:00:00Z",
            "SeriesList": SERIES,
            "TypeName": "gw.weather.forecast",
            "Version": "001",
        },
        auto_upgrade=False,
        expect=GwWeatherForecast001,
    )


def persistor() -> GwWeatherForecastPersistor:
    return GwWeatherForecastPersistor(
        logging.getLogger("test_weather_forecast_message_id")
    )


def test_002_row_id_is_the_forecast_uid():
    received = datetime.now(tz=UTC)
    infos = {
        b: persistor().persist_v002(FROM_ALIAS, received, forecast_002(b)) for b in UIDS
    }
    assert {b: i.id for b, i in infos.items()} == UIDS
    assert {i.created_at for i in infos.values()} == {CREATED_AT}


def test_001_rows_of_one_slot_are_distinct_and_path_independent():
    p = persistor()
    received = datetime.now(tz=UTC)
    ids = {b: p.persist_v001(FROM_ALIAS, received, forecast_001(b)).id for b in UIDS}
    assert len(set(ids.values())) == 3
    later = received + timedelta(hours=6)
    assert {
        b: p.persist_v001(FROM_ALIAS, later, forecast_001(b)).id for b in UIDS
    } == ids
    assert (
        p.persist_v001(
            FROM_ALIAS, received, forecast_001("us.me.millinocket.moose")
        ).created_at
        == CREATED_AT
    )


def test_dispatch_reaches_both_versions():
    sp = SemaMessagePersistor.__new__(SemaMessagePersistor)
    sp.logger = logging.getLogger("test_weather_forecast_message_id")
    sp.custom_persistor_lookup = {p.target_message_type: p for p in [persistor()]}
    received = datetime.now(tz=UTC)
    for payload in (
        forecast_001("us.me.millinocket.moose"),
        forecast_002("us.me.millinocket.moose"),
    ):
        custom = sp.custom_persistor_lookup[payload.type_name]
        info = getattr(custom, f"persist_v{payload.version}")(
            FROM_ALIAS, received, payload
        )
        assert info.created_at == CREATED_AT
