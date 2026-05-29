"""Smoke tests for the post-Stage-1 JournalKeeper."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from gjk.journal_keeper import JournalKeeper
from gwbase.actor_base import ActorBase


def test_module_imports() -> None:
    """The new JournalKeeper imports cleanly (no leftover doomed-module deps)."""
    assert JournalKeeper is not None


def test_inherits_actor_base() -> None:
    """Journalkeeper is not a GNode actor — it must inherit ActorBase, not
    GridworksActor."""
    assert issubclass(JournalKeeper, ActorBase)


def _make_bare_jk() -> JournalKeeper:
    """Construct a JournalKeeper that skips ActorBase.__init__ (which needs
    a g_node.json on disk). Lets us unit-test dispatch_message in isolation."""
    jk = JournalKeeper.__new__(JournalKeeper)
    jk.codec = MagicMock()
    jk.persistor = MagicMock()
    jk.logger = MagicMock()
    return jk


def test_dispatch_message_malformed_json_does_not_raise() -> None:
    """Bad JSON gets logged and swallowed; the live actor must keep running."""
    jk = _make_bare_jk()
    envelope = MagicMock(from_alias="test.alias")
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

    envelope = MagicMock(from_alias="test.alias")
    body = json.dumps({
        "Payload": {"TypeName": "weather.forecast", "Version": "000"}
    }).encode()
    jk.dispatch_message(envelope=envelope, body=body)

    jk.persistor.persist_message.assert_called_once()
    args, _ = jk.persistor.persist_message.call_args
    assert args[0] == "test.alias"
    assert args[2] is sema_obj


def test_dispatch_message_degraded_type_not_persisted() -> None:
    """Degraded SemaType is logged but not persisted."""
    jk = _make_bare_jk()
    degraded = MagicMock()  # not a SemaType instance
    degraded.type_name = "unknown.thing"
    degraded.version = "000"
    jk.codec.from_dict.return_value = degraded

    envelope = MagicMock(from_alias="test.alias")
    body = json.dumps({"Payload": {"TypeName": "unknown.thing"}}).encode()
    jk.dispatch_message(envelope=envelope, body=body)

    jk.persistor.persist_message.assert_not_called()
    jk.logger.warning.assert_called()
