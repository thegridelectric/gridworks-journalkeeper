"""gw.scada.commit, the commit a scada announces once per run at boot, is
journaled in the messages table at its own MessageCreatedMs, so the row
dedupes between the rabbit path and an S3 import. Hermetic, no DB."""

from datetime import UTC, datetime, timedelta

from gjk.sema import SemaCodec
from gjk.sema.types import GwScadaCommit
from gjk.sema_message_persistor import SemaMessagePersistor

ALIAS = "hw1.isone.me.versant.keene.beech.scada"
CREATED_MS = 1790000000000
COMMIT = {
    "ScadaAlias": ALIAS,
    "GitCommit": "109d44041c2b3d4e5f60718293a4b5c6d7e8f901",
    "MessageCreatedMs": CREATED_MS,
    "TypeName": "gw.scada.commit",
    "Version": "000",
}


def _persistor() -> SemaMessagePersistor:
    p = SemaMessagePersistor.__new__(SemaMessagePersistor)
    p.custom_persistor_lookup = {}
    return p


def _commit() -> GwScadaCommit:
    decoded = SemaCodec().from_dict(COMMIT, auto_upgrade=False)
    assert isinstance(decoded, GwScadaCommit)
    return decoded


def test_scada_commit_is_captured_and_dedupable():
    p = _persistor()
    assert "gw.scada.commit" in p.all_known_message_types()
    assert "gw.scada.commit" in p.dedupable_message_types()


def test_scada_commit_is_journaled_at_its_own_created_time():
    p = _persistor()
    received = datetime.now(UTC)
    info = p.persist_message_default(ALIAS, _commit(), received)
    assert info.created_at == datetime.fromtimestamp(CREATED_MS / 1000, tz=UTC)
    later = p.persist_message_default(ALIAS, _commit(), received + timedelta(hours=1))
    assert later.id == info.id
