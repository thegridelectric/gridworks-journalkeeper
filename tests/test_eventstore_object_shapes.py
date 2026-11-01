"""An eventstore object is either the word itself, as the ear stores a
gwbase message, or a scada's MQTT-era envelope whose Payload is the word.
The importer decodes both."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import gjk.s3_message_importer as imp_mod

SAMPLES = Path(imp_mod.__file__).parent / "sema" / "samples"
FIXTURES = Path(__file__).parent / "data"
LOG = logging.getLogger("test_eventstore_object_shapes")


class Info:
    def __init__(self, key: str):
        self.key_str = key
        self.from_alias, self.msg_type_name = key.split("/")[-1].split("-")[:2]
        self.persist_time = datetime(2026, 10, 18, tzinfo=UTC)


class Importer:
    def __init__(self, *_a, **_k):
        self.objects = {
            "hw1__1/eventstore/20261018/hw1.isone.weather-gw.weather.forecast-1792281667848-hw1.ear.json": (
                SAMPLES / "gw.weather.forecast.002.json"
            ).read_bytes(),
            "hw1__1/eventstore/20261018/hw1.isone.me.versant.keene.beech-gridworks.ack-1779926400685-ear.json": (
                FIXTURES / "gridworks_ack_s3_object.json"
            ).read_bytes(),
        }

    def find_messages_in_date_range(self, start, end):  # noqa: ARG002
        return [Info(key) for key in self.objects]

    def download_message(self, info):
        body = self.objects[info.key_str]
        return body, len(body)

    prefetch = imp_mod.S3MessageImporter.prefetch


class Persistor:
    custom_persistor_lookup: dict = {}
    RECEIPT_TIME_KEYED_TYPES: frozenset = frozenset()

    def __init__(self, *_a, **_k):
        pass

    def all_known_message_types(self):
        return {"gw.weather.forecast", "gridworks.ack"}

    def dedupable_message_types(self):
        return self.all_known_message_types()


def test_dry_run_decodes_a_bare_word_and_an_envelope(monkeypatch, tmp_path):
    monkeypatch.setattr(imp_mod, "Settings", lambda **_k: object())
    monkeypatch.setattr(imp_mod, "SemaMessagePersistor", Persistor)
    monkeypatch.setattr(imp_mod, "S3MessageImporter", Importer)
    summary = tmp_path / "summary.json"
    imp_mod.main([
        "--start",
        "2026-10-18",
        "--end",
        "2026-10-18",
        "--dry-run",
        "--summary-json",
        str(summary),
    ])
    outcomes = {
        row["type_name"]: {k: row[k] for k in ("ok", "degraded", "failed")}
        for row in json.loads(summary.read_text())["versions"]
    }
    assert outcomes["gw.weather.forecast"] == {"ok": 1, "degraded": 0, "failed": 0}
    # The ack is not in this snapshot, so it decodes degraded; what matters
    # is that the envelope's word reached the codec.
    assert outcomes["gridworks.ack"] == {"ok": 0, "degraded": 1, "failed": 0}
