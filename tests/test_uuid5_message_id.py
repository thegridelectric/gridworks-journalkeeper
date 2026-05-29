"""Tests for the deterministic uuid5 message id (jm/idempotent-msg-id).

`persist_message_default` derives the id as
`uuid5(MESSAGE_ID_NAMESPACE, "{from_alias}|{type_name}|{persisted_ms}")` for any
message type without a `MSG_ID_FIELDS` entry — making re-import of the same S3
object a true no-op. These tests use a real `gridworks.ack` S3 object captured in
`tests/data/`. (It decodes to a DegradedSemaType here because `gridworks.ack`
isn't in this snapshot's seed; that's irrelevant to the id logic, which only
reads `type_name`.)
"""

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from gjk.sema import SemaCodec
from gjk.sema_message_persistor import MESSAGE_ID_NAMESPACE, SemaMessagePersistor

# From the S3 key of the captured object:
# hw1...beech-gridworks.ack-1779926400685-ear...json
FROM_ALIAS = "hw1.isone.me.versant.keene.beech"
PERSISTED_MS = 1779926400685
FIXTURE = Path(__file__).parent / "data" / "gridworks_ack_s3_object.json"


def _payload():
    obj = SemaCodec().from_dict(
        json.loads(FIXTURE.read_text())["Payload"], auto_upgrade=False, mode="degraded"
    )
    assert obj.type_name == "gridworks.ack"
    return obj


def _persistor():
    # bypass __init__ so we don't need a DB engine — persist_message_default
    # only reads class-level field maps + payload.type_name + time_received.
    p = SemaMessagePersistor.__new__(SemaMessagePersistor)
    p.logger = logging.getLogger("test_uuid5")
    return p


def test_uuid5_is_deterministic_and_matches_formula():
    payload, persistor = _payload(), _persistor()
    t = datetime.fromtimestamp(PERSISTED_MS / 1000, tz=UTC)

    id1 = persistor.persist_message_default(FROM_ALIAS, payload, t).id
    id2 = persistor.persist_message_default(FROM_ALIAS, payload, t).id

    assert id1 == id2  # same inputs -> same id (idempotent re-import)
    expected = str(
        uuid.uuid5(
            MESSAGE_ID_NAMESPACE,
            f"{FROM_ALIAS}|{payload.type_name}|{int(t.timestamp() * 1000)}",
        )
    )
    assert id1 == expected


def test_uuid5_varies_with_persisted_ms():
    payload, persistor = _payload(), _persistor()
    t1 = datetime.fromtimestamp(PERSISTED_MS / 1000, tz=UTC)
    t2 = datetime.fromtimestamp((PERSISTED_MS + 1000) / 1000, tz=UTC)

    id1 = persistor.persist_message_default(FROM_ALIAS, payload, t1).id
    id2 = persistor.persist_message_default(FROM_ALIAS, payload, t2).id

    assert id1 != id2  # a different object (different ms) gets a different id
