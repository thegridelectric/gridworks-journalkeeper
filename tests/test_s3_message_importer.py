"""Tests for the s3_message_importer robustness fixes (jm/importer-robustness).

Hermetic — no AWS, no DB. Covers:
  A. find_messages_on_date tolerates a page with no "Contents" (empty/missing
     date folder) instead of raising KeyError.
  B. main()'s per-message loop continues past a failing message instead of
     aborting the whole run.
"""

import logging
from datetime import UTC, datetime

import gjk.s3_message_importer as imp_mod
from gjk.s3_message_importer import S3MessageImporter

LOG = logging.getLogger("test_s3_message_importer")


class _FakePaginator:
    def __init__(self, pages):
        self._pages = pages

    def paginate(self, **_kwargs):
        return iter(self._pages)


class _FakeS3:
    def __init__(self, pages):
        self._pages = pages

    def get_paginator(self, _name):
        return _FakePaginator(self._pages)


def _importer(pages, msg_types):
    """Build an importer with a fake S3 client, bypassing __init__/boto3."""
    imp = S3MessageImporter.__new__(S3MessageImporter)
    imp.settings = None
    imp.s3 = _FakeS3(pages)
    imp.aws_bucket_name = "gwdev"
    imp.world_instance_name = "hw1__1"
    imp.msg_types = msg_types
    imp.logger = LOG
    return imp


# --- A: empty / missing date folder ---------------------------------------

def test_find_messages_on_date_empty_page_does_not_raise():
    # list_objects_v2 omits "Contents" entirely for a date with no objects.
    imp = _importer(pages=[{}], msg_types={"snapshot.spaceheat"})
    assert list(imp.find_messages_on_date(datetime(2030, 1, 1, tzinfo=UTC))) == []


def test_find_messages_on_date_yields_matching_contents():
    key = (
        "hw1__1/eventstore/20260523/"
        "beech-snapshot.spaceheat-1779000000000-ear.json"
    )
    imp = _importer(
        pages=[{"Contents": [{"Key": key}]}], msg_types={"snapshot.spaceheat"}
    )
    out = list(imp.find_messages_on_date(datetime(2026, 5, 23, tzinfo=UTC)))
    assert len(out) == 1
    assert out[0].msg_type_name == "snapshot.spaceheat"


# --- B: a failing message must not abort the run ---------------------------

class _FakeInfo:
    def __init__(self, key):
        self.key_str = key
        self.from_alias = "alias"
        self.msg_type_name = "x"
        self.persist_time = datetime(2026, 5, 23, tzinfo=UTC)


class _FakeImporter:
    def __init__(self, *_a, **_k):
        self.download_calls = 0

    def find_messages_in_date_range(self, start, end):  # noqa: ARG002
        return [_FakeInfo("k1"), _FakeInfo("k2")]

    def download_message(self, _info):
        self.download_calls += 1
        raise RuntimeError("boom")  # every message fails


class _FakePersistor:
    def __init__(self, *_a, **_k):
        pass

    def all_known_message_types(self):
        return set()

    def persist_message(self, *_a, **_k):
        pass


def test_main_continues_past_failed_message(monkeypatch):
    fake_importer = _FakeImporter()
    monkeypatch.setattr(imp_mod, "Settings", lambda **_k: object())
    monkeypatch.setattr(imp_mod, "SemaCodec", lambda *_a, **_k: object())
    monkeypatch.setattr(imp_mod, "SemaMessagePersistor", _FakePersistor)
    monkeypatch.setattr(imp_mod, "S3MessageImporter", lambda *_a, **_k: fake_importer)

    imp_mod.main()

    # Both messages were attempted: the loop did NOT `return` on the first
    # failure (the fix is `continue`). Pre-fix this would be 1.
    assert fake_importer.download_calls == 2
