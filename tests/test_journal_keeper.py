"""Smoke tests for the post-Stage-1 JournalKeeper."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from gjk.journal_keeper import JournalKeeper
from gwbase.actor_base import ActorBase
from gwbase.transport_encoding import WrappedRoutingEnvelope
from gwbase.wrapped import wrap_bytes


def test_module_imports() -> None:
    """The new JournalKeeper imports cleanly (no leftover doomed-module deps)."""
    assert JournalKeeper is not None


def test_inherits_actor_base() -> None:
    """Journalkeeper is not a GNode actor — it must inherit ActorBase, not
    GridworksActor."""
    assert issubclass(JournalKeeper, ActorBase)


def _make_bare_jk() -> JournalKeeper:
    """Construct a JournalKeeper that skips ActorBase.__init__ (which opens a
    live rabbit connection). Lets us unit-test dispatch_message in isolation."""
    jk = JournalKeeper.__new__(JournalKeeper)
    jk.codec = MagicMock()
    jk.persistor = MagicMock()
    jk.logger = MagicMock()
    # The capture set the queue-wide `#` bind narrows against at dispatch.
    jk._known_types = frozenset({
        "weather.forecast",
        "unknown.thing",
        "glitch",
        "flo.next.hour.plans",
    })
    return jk


def test_dispatch_message_malformed_json_does_not_raise() -> None:
    """Bad JSON gets logged and swallowed; the live actor must keep running."""
    jk = _make_bare_jk()
    envelope = MagicMock(from_alias="test.alias", type_name="weather.forecast")
    jk.dispatch_message(envelope=envelope, body=b"not-json")
    jk.persistor.persist_message.assert_not_called()
    jk.logger.error.assert_called()


def test_dispatch_message_routes_sema_to_persistor() -> None:
    """A well-formed Payload reaches persistor.persist_message."""
    from gjk.sema import SemaType

    jk = _make_bare_jk()
    sema_obj = MagicMock(spec=SemaType)
    sema_obj.type_name = "weather.forecast"
    sema_obj.version = "000"
    jk.codec.from_dict.return_value = sema_obj

    envelope = MagicMock(from_alias="test.alias", type_name="weather.forecast")
    payload = {"TypeName": "weather.forecast", "Version": "000"}
    jk.dispatch_message(envelope=envelope, body=json.dumps(payload).encode())

    jk.codec.from_dict.assert_called_once()
    assert jk.codec.from_dict.call_args[0][0] == payload
    jk.persistor.persist_message.assert_called_once()
    args, _ = jk.persistor.persist_message.call_args
    assert args[0] == "test.alias"
    assert args[2] is sema_obj


def _wrapped_envelope(type_name: str) -> MagicMock:
    env = MagicMock(spec=WrappedRoutingEnvelope)
    env.from_alias = "d1.isone.me.versant.keene.beech.scada"
    env.type_name = type_name
    return env


def test_dispatch_message_unwraps_a_gw_delivery() -> None:
    """A `gw` routing key means a wrapped body: the codec sees the inner
    payload, never the envelope."""
    from gjk.sema import SemaType

    jk = _make_bare_jk()
    sema_obj = MagicMock(spec=SemaType)
    sema_obj.type_name = "glitch"
    sema_obj.version = "000"
    jk.codec.from_dict.return_value = sema_obj

    inner = {"TypeName": "glitch", "Version": "000"}
    body = wrap_bytes(
        src="d1.isone.me.versant.keene.beech.scada",
        dst="d1.journal",
        inner_type_name="glitch",
        inner_payload_dict=inner,
    )
    jk.dispatch_message(envelope=_wrapped_envelope("glitch"), body=body)

    assert jk.codec.from_dict.call_args[0][0] == inner
    jk.persistor.persist_message.assert_called_once()
    assert jk.persistor.persist_message.call_args[0][0] == (
        "d1.isone.me.versant.keene.beech.scada"
    )


def test_dispatch_message_drops_a_gw_delivery_whose_header_disagrees() -> None:
    """The header's MessageType must be the routing key's type."""
    jk = _make_bare_jk()
    body = wrap_bytes(
        src="d1.isone.me.versant.keene.beech.scada",
        dst="d1.journal",
        inner_type_name="weather.forecast",
        inner_payload_dict={"TypeName": "weather.forecast", "Version": "000"},
    )
    jk.dispatch_message(envelope=_wrapped_envelope("glitch"), body=body)

    jk.codec.from_dict.assert_not_called()
    jk.persistor.persist_message.assert_not_called()
    jk.logger.error.assert_called()


def test_dispatch_message_drops_a_gw_delivery_that_is_not_an_envelope() -> None:
    """A `gw` key over a bare body is a malformed delivery, not a payload."""
    jk = _make_bare_jk()
    body = json.dumps({"TypeName": "glitch", "Version": "000"}).encode()
    jk.dispatch_message(envelope=_wrapped_envelope("glitch"), body=body)

    jk.codec.from_dict.assert_not_called()
    jk.persistor.persist_message.assert_not_called()
    jk.logger.error.assert_called()


def test_dispatch_message_does_not_sniff_a_bare_body_for_payload() -> None:
    """On an `rj` / `rjb` key the body is the sema dict as sent; a `Payload`
    key inside it is the sender's, not an envelope to open."""
    from gjk.sema import SemaType

    jk = _make_bare_jk()
    sema_obj = MagicMock(spec=SemaType)
    sema_obj.type_name = "glitch"
    sema_obj.version = "000"
    jk.codec.from_dict.return_value = sema_obj

    payload = {"TypeName": "glitch", "Version": "000", "Payload": {"x": 1}}
    envelope = MagicMock(from_alias="test.alias", type_name="glitch")
    jk.dispatch_message(envelope=envelope, body=json.dumps(payload).encode())

    assert jk.codec.from_dict.call_args[0][0] == payload


def test_dispatch_message_outside_capture_set_drops_before_decode() -> None:
    """The `#` bind delivers the whole bus; a type outside the capture set
    returns before any body decode."""
    jk = _make_bare_jk()
    envelope = MagicMock(from_alias="test.alias", type_name="gridworks.ping")
    jk.dispatch_message(envelope=envelope, body=b"irrelevant")
    jk.codec.from_dict.assert_not_called()
    jk.persistor.persist_message.assert_not_called()


def test_persist_payload_gates_decodable_but_uncaptured_types() -> None:
    """The legacy_hack path has no envelope to pre-gate on: a decodable
    type outside the capture set must still not persist (decodable ≠
    captured — the snapshot deliberately holds vocabulary gjk does not
    persist, e.g. bid)."""
    from gjk.sema import SemaType

    jk = _make_bare_jk()
    sema_obj = MagicMock(spec=SemaType)
    sema_obj.type_name = "bid"
    sema_obj.version = "000"
    jk.codec.from_dict.return_value = sema_obj

    jk._persist_payload(
        from_alias="test.alias", payload={"TypeName": "bid", "Version": "000"}
    )

    jk.persistor.persist_message.assert_not_called()


def test_dispatch_message_degraded_type_not_persisted() -> None:
    """Degraded SemaType is logged but not persisted."""
    jk = _make_bare_jk()
    degraded = MagicMock()  # not a SemaType instance
    degraded.type_name = "unknown.thing"
    degraded.version = "000"
    jk.codec.from_dict.return_value = degraded

    envelope = MagicMock(from_alias="test.alias", type_name="unknown.thing")
    body = json.dumps({"TypeName": "unknown.thing"}).encode()
    jk.dispatch_message(envelope=envelope, body=body)

    jk.persistor.persist_message.assert_not_called()
    jk.logger.warning.assert_called()


def test_legacy_hack_persists_broadcast_key() -> None:
    """legacy_hack: a pre-gwbase `broadcast.*` key (which gwbase cannot parse)
    is persisted anyway, with from_alias taken from the wrapped body's
    Header.Src (the legacy key has no from-alias slot)."""
    from gjk.sema import SemaType

    jk = _make_bare_jk()
    sema_obj = MagicMock(spec=SemaType)
    sema_obj.type_name = "flo.next.hour.plans"
    sema_obj.version = "000"
    jk.codec.from_dict.return_value = sema_obj

    body = json.dumps({
        "Header": {"Src": "hw1.isone.me.versant.keene.beech.ltn"},
        "Payload": {"TypeName": "flo.next.hour.plans", "Version": "000"},
    }).encode()
    jk.on_routing_key_parse_error(
        routing_key="broadcast.flo-next-hour-plans", body=body, error=ValueError("x")
    )

    jk.persistor.persist_message.assert_called_once()
    args, _ = jk.persistor.persist_message.call_args
    assert args[0] == "hw1.isone.me.versant.keene.beech.ltn"
    assert args[2] is sema_obj


def test_legacy_hack_src_falls_back_when_header_missing() -> None:
    """No Header.Src in the body → a sentinel source, still persisted."""
    from gjk.sema import SemaType

    jk = _make_bare_jk()
    sema_obj = MagicMock(spec=SemaType)
    sema_obj.type_name = "glitch"
    sema_obj.version = "000"
    jk.codec.from_dict.return_value = sema_obj

    body = json.dumps({"Payload": {"TypeName": "glitch", "Version": "000"}}).encode()
    jk.on_routing_key_parse_error(
        routing_key="broadcast.glitch", body=body, error=ValueError("x")
    )

    jk.persistor.persist_message.assert_called_once()
    assert jk.persistor.persist_message.call_args[0][0] == "unknown.broadcast.src"


@pytest.mark.skipif(
    not hasattr(ActorBase, "on_routing_key_parse_error"),
    reason="needs the gridworks-base branch with the on_message parse-error hook",
)
def test_legacy_hack_falls_back_for_non_broadcast() -> None:
    """A non-broadcast parse error is NOT treated as legacy data — it defers to
    the base hook (log+drop) and does not persist."""
    jk = _make_bare_jk()
    jk.on_routing_key_parse_error(
        routing_key="rj.garbled.key", body=b"{}", error=ValueError("x")
    )
    jk.persistor.persist_message.assert_not_called()
