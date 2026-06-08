"""Tests for deterministic (uuid5) message ids in the custom persistors
(jm/custom-persistor-idempotency).

flo.params.house0 and weather.forecast previously minted messages.id with
uuid4(), defeating the re-import idempotency the default path got in 7308766.
They now derive the id via the shared default_message_id(...). These hermetic
tests prove (A) the id is deterministic per persistor, and (B) the dispatch seam
threads time_received through to the custom persistor (the actual root cause).
No DB/AWS.
"""

import logging
from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import MagicMock

from gjk.flo_params_house0_persistor import FloParamsHouse0Persistor
from gjk.message_persistence_info import MessagePersistenceInfo, default_message_id
from gjk.sema_message_persistor import SemaMessagePersistor
from gjk.weather_forecast_persistor import WeatherForecastPersistor

FROM_ALIAS = "hw1.isone.me.versant.keene.beech.scada"
PERSISTED_MS = 1779926400685


def _t(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=UTC)


def test_weather_persistor_id_is_deterministic_uuid5():
    p = WeatherForecastPersistor(logging.getLogger("test_custom_persistor"))
    forecast = MagicMock(forecast_created_s=1779926000)
    t = _t(PERSISTED_MS)

    id1 = p.persist_v000(FROM_ALIAS, t, forecast).id
    id2 = p.persist_v000(FROM_ALIAS, t, forecast).id

    assert id1 == id2  # same inputs -> same id (idempotent re-import)
    assert id1 == default_message_id(FROM_ALIAS, "weather.forecast", t)
    # a different persisted ms -> a different id
    assert p.persist_v000(FROM_ALIAS, _t(PERSISTED_MS + 1000), forecast).id != id1


def test_flo_persistor_id_is_deterministic_uuid5():
    p = FloParamsHouse0Persistor(logging.getLogger("test_custom_persistor"))
    flo = MagicMock(params_generated_s=1779926000)
    t = _t(PERSISTED_MS)

    id1 = p.persist_v007(FROM_ALIAS, t, flo).id
    id2 = p.persist_v007(FROM_ALIAS, t, flo).id

    assert id1 == id2
    assert id1 == default_message_id(FROM_ALIAS, "flo.params.house0", t)
    assert p.persist_v007(FROM_ALIAS, _t(PERSISTED_MS + 1000), flo).id != id1


def test_dispatch_threads_time_received_to_custom_persistor():
    """Regression guard for the root cause: persist_message MUST pass
    time_received to the custom persistor's persist_vNNN."""
    p = SemaMessagePersistor.__new__(SemaMessagePersistor)
    p.logger = logging.getLogger("test_custom_persistor")

    t = _t(PERSISTED_MS)
    custom = MagicMock()
    custom.persist_v000.return_value = MessagePersistenceInfo(
        id=default_message_id(FROM_ALIAS, "weather.forecast", t),
        created_at=None,
    )
    p.custom_persistor_lookup = {"weather.forecast": custom}

    @contextmanager
    def _fake_db():
        yield MagicMock()

    p.get_db = _fake_db

    payload = MagicMock(version="000")
    payload.type_name = "weather.forecast"
    payload.to_dict.return_value = {}

    p.persist_message(FROM_ALIAS, t, payload)

    custom.persist_v000.assert_called_once_with(FROM_ALIAS, t, payload)
