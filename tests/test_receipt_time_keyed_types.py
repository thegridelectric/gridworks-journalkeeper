"""Static pin of the types the S3 importer refuses, and why.

A messages row is keyed (timestamp, id). Both halves come from the payload
only when it carries a created time (the id is derived from it when the
payload has no id of its own); otherwise the receipt time leaks into the
key and the same message arriving by rabbit and by S3 import gets two rows.
So the S3 importer persists only types with a created time. This test pins
the excluded set: a new word lands here deliberately, never by accident.
"""

from gjk.sema_message_persistor import SemaMessagePersistor

EXPECTED = frozenset({
    "atn.bid",
    "gw.weather.channel.gt",
    "gw.weather.cmd.ack",
    "gw.weather.cmd.nack",
    "gw.weather.create.cmd",
    "gw.weather.forecast.bundle.gt",
    "gw.weather.forecast.channel.gt",
    "gw.weather.location.gt",
    "gw.weather.observation",
    "latest.price",
    "power.watts",
})


def _persistor() -> SemaMessagePersistor:
    p = SemaMessagePersistor.__new__(SemaMessagePersistor)
    p.custom_persistor_lookup = {}
    return p


def test_receipt_time_keyed_types_are_exactly_the_expected_set():
    assert SemaMessagePersistor.RECEIPT_TIME_KEYED_TYPES == EXPECTED


def test_every_type_with_a_created_time_field_is_dedupable():
    with_created = set(SemaMessagePersistor.MSG_CREATED_AT_FIELDS_MS) | set(
        SemaMessagePersistor.MSG_CREATED_AT_FIELDS_S
    )
    assert not (with_created & SemaMessagePersistor.RECEIPT_TIME_KEYED_TYPES)


def test_every_basic_type_is_receipt_time_keyed():
    assert (
        set(SemaMessagePersistor.BASIC_MSG_TYPES)
        <= SemaMessagePersistor.RECEIPT_TIME_KEYED_TYPES
    )


def test_id_only_types_are_receipt_time_keyed():
    id_only = (
        set(SemaMessagePersistor.MSG_ID_FIELDS)
        - set(SemaMessagePersistor.MSG_CREATED_AT_FIELDS_MS)
        - set(SemaMessagePersistor.MSG_CREATED_AT_FIELDS_S)
    )
    assert id_only <= SemaMessagePersistor.RECEIPT_TIME_KEYED_TYPES


def test_dedupable_excludes_the_set():
    p = _persistor()
    assert not (p.dedupable_message_types() & EXPECTED)
    assert "report.event" not in EXPECTED
