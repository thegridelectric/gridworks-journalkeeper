"""Undecodable messages have their S3 key logged (not payload), so they can
be re-fetched from the eventstore later — e.g. the fractional-temp
flo.params.house0 messages, for the int-vs-float decision.
"""

import json
from datetime import UTC, datetime

from gjk.s3_message_importer import S3MessageInfo, log_reject

KEY = "hw1__1/eventstore/20250328/hw1.isone.me.versant.keene.oak.scada-flo.params.house0-1743159477125-ear.json"


def test_reject_logs_key_and_context_not_payload(tmp_path):
    f = tmp_path / "rejects.jsonl"
    log_reject(f, S3MessageInfo(KEY), ValueError("Input should be a valid integer"))

    (line,) = f.read_text().splitlines()
    rec = json.loads(line)
    assert rec == {
        "key": KEY,
        "from_alias": "hw1.isone.me.versant.keene.oak.scada",
        "type_name": "flo.params.house0",
        "persisted_at": datetime.fromtimestamp(1743159477.125, UTC).isoformat(),
        "error": repr(ValueError("Input should be a valid integer")),
    }
    assert "payload" not in rec  # keys only; re-fetch from S3 on demand


def test_reject_log_appends(tmp_path):
    f = tmp_path / "r.jsonl"
    log_reject(f, S3MessageInfo(KEY), ValueError("x"))
    log_reject(f, S3MessageInfo(KEY), ValueError("y"))
    assert len(f.read_text().splitlines()) == 2
