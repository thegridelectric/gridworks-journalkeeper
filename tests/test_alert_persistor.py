"""The alerter's words in the capture set, and `gw.alert` at its own time."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

from gjk.alert_persistor import AlertPersistor
from gjk.sema.codec import SemaCodec
from gjk.sema.enums import GwAlertState
from gjk.sema.types import GwAlert, GwHackAlertSilences
from gjk.sema_message_persistor import SemaMessagePersistor

RAISED_MS = 1792079886718
RESOLVED_MS = RAISED_MS + 600_000


def _firing() -> GwAlert:
    return GwAlert(
        src="hw1.alerts",
        category="House",
        kind="NoData",
        state=GwAlertState.Firing,
        alert_id="cbbd9bad-cceb-4c23-b8b2-95f9f79102a0",
        about_g_node_alias="hw1.isone.me.versant.keene.elm.ta",
        raised_ms=RAISED_MS,
        summary="no data for 600 s",
    )


def _resolved() -> GwAlert:
    firing = _firing()
    return firing.model_copy(
        update={"state": GwAlertState.Resolved, "resolved_ms": RESOLVED_MS}
    )


def test_alerter_words_are_in_the_capture_set() -> None:
    p = SemaMessagePersistor.__new__(SemaMessagePersistor)
    p.custom_persistor_lookup = {"gw.alert": AlertPersistor(MagicMock())}
    known = p.all_known_message_types()
    assert "gw.alert" in known
    assert "gw.hack.alert.silences" in known


def test_alerter_words_decode_from_the_snapshot() -> None:
    codec = SemaCodec()
    alert = codec.from_dict(_firing().to_dict(), auto_upgrade=False)
    assert isinstance(alert, GwAlert)
    silences = codec.from_dict(
        GwHackAlertSilences(
            src="hw1.alerts",
            silenced_g_node_aliases=["hw1.isone.me.versant.keene.elm.ta"],
        ).to_dict(),
        auto_upgrade=False,
    )
    assert isinstance(silences, GwHackAlertSilences)


def test_firing_record_is_created_at_raised_ms() -> None:
    info = AlertPersistor(MagicMock()).persist_v000(
        "hw1.alerts", datetime.now(UTC), _firing()
    )
    assert info.created_at == datetime.fromtimestamp(RAISED_MS / 1000, tz=UTC)


def test_resolved_record_is_created_at_resolved_ms_and_is_its_own_row() -> None:
    persistor = AlertPersistor(MagicMock())
    now = datetime.now(UTC)
    firing = persistor.persist_v000("hw1.alerts", now, _firing())
    resolved = persistor.persist_v000("hw1.alerts", now, _resolved())
    assert resolved.created_at == datetime.fromtimestamp(RESOLVED_MS / 1000, tz=UTC)
    assert resolved.id != firing.id


def test_record_id_does_not_depend_on_receipt_time() -> None:
    persistor = AlertPersistor(MagicMock())
    a = persistor.persist_v000(
        "hw1.alerts", datetime(2026, 1, 1, tzinfo=UTC), _firing()
    )
    b = persistor.persist_v000(
        "hw1.alerts", datetime(2026, 6, 1, tzinfo=UTC), _firing()
    )
    assert a.id == b.id
