"""Retired word versions are refused before decode on both paths."""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock

from gjk.retired_versions import RETIRED_VERSIONS, is_retired
from gjk.s3_message_importer import RunSummary, S3MessageInfo
from gjk.sema import SemaCodec

SAMPLES = Path(__file__).resolve().parents[1] / "src" / "gjk" / "sema" / "samples"


def test_retired_versions_are_absent_from_the_snapshot() -> None:
    """The snapshot refuses every retired version on its own; the table
    only names the refusal."""
    codec = SemaCodec()
    for type_name, versions in RETIRED_VERSIONS.items():
        assert type_name in codec.registry, type_name
        carried = {codec.registry[type_name].version_value()} | set(
            codec.old_versions.get(type_name, {})
        )
        assert not versions & carried, (type_name, versions & carried)


def test_is_retired_names_only_the_table() -> None:
    assert is_retired({"TypeName": "gw.weather.forecast", "Version": "000"})
    assert not is_retired({"TypeName": "gw.weather.forecast", "Version": "001"})
    assert not is_retired({"TypeName": "weather.forecast", "Version": "000"})
    assert not is_retired({"Version": "000"})


def test_live_path_drops_a_retired_version_before_decode() -> None:
    from gjk.journal_keeper import JournalKeeper

    jk = MagicMock(spec=JournalKeeper)
    jk.logger = logging.getLogger("test_retired")
    jk.codec = MagicMock()
    jk.persistor = MagicMock()
    JournalKeeper._persist_payload(
        jk,
        from_alias="hw1.weather",
        payload={"TypeName": "gw.weather.observation", "Version": "000"},
    )
    jk.codec.from_dict.assert_not_called()
    jk.persistor.persist_message.assert_not_called()


def test_run_summary_counts_retired() -> None:
    summary = RunSummary()
    info = S3MessageInfo(
        "hw1.weather-gw.weather.forecast-1760000000000-ear.electricity.works.json"
    )
    summary.count(info, "gw.weather.forecast", "000", "retired")
    assert summary.versions[("gw.weather.forecast", "000")].retired == 1
    row = json.loads(json.dumps(summary.to_jsonable()))["versions"][0]
    assert row["retired"] == 1 and row["ok"] == 0
