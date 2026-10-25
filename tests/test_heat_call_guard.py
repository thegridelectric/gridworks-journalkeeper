"""A layout that declares heat-call as a DerivedChannel has a scada that
reports the readings itself: the journal makes no pseudo channel of the
same name, and a report that carries heat-call readings gets none
synthesized from its whitewire-pwr readings. A house whose layout declares
no heat-call channel keeps the synthesis. Hermetic, no DB."""

import json
import logging
import uuid
from pathlib import Path
from unittest.mock import MagicMock

from gw_data.db.models import ReadingChannelSql

from gjk.report_event_persistor import ReportEventPersistor
from gjk.sema import SemaCodec
from gjk.sema.enums import Gw1Unit, GwChannelKind
from gjk.zone_heat_call_pseudo_channel import ZoneHeatCallPseudoChannel

SAMPLES = Path(__file__).parent / "data" / "sample_messages"
# willow1 declares zone1-main-heat-call as a DerivedChannel over
# zone1-main-whitewire-pwr; beech on 011 declares whitewire-pwr only.
WILLOW_013 = SAMPLES / "ops392" / "willow1-layout.lite-013-2026-10-22.json"
BEECH_011 = SAMPLES / "ops498" / "beech-layout.lite-011-2026-07-25.json"
BEECH_REPORT = SAMPLES / "ops498" / "beech-report.event-002-2025-10-13.json"
TA = "hw1.isone.me.versant.keene.beech.ta"
ALIAS = "hw1.isone.me.versant.keene.beech.scada"
WHITEWIRE = "zone1-down-whitewire-pwr"
HEAT_CALL = "zone1-down-heat-call"


def layout(path: Path):
    return SemaCodec().from_dict(json.loads(path.read_text()), auto_upgrade=False)


def heat_call_pseudo_names(path: Path) -> set[str]:
    return {
        pc.name
        for pc in ReportEventPersistor.get_pseudo_channels(layout(path))
        if isinstance(pc, ZoneHeatCallPseudoChannel)
    }


def channel(name: str, unit: str, unit_type: str, channel_type: str):
    return ReadingChannelSql(
        id=uuid.uuid4(),
        name=name,
        terminal_asset_alias=TA,
        display_name=name,
        unit=unit,
        unit_type=unit_type,
        channel_type=channel_type,
        deactivated_date=None,
    )


def beech_report(extra_readings: list[dict] | None = None):
    d = json.loads(BEECH_REPORT.read_text())
    d["Report"]["ChannelReadingList"] += extra_readings or []
    return SemaCodec().from_dict(d, auto_upgrade=False)


def readings_by_channel(rows: list[ReadingChannelSql], report) -> dict:
    persistor = ReportEventPersistor(logging.getLogger("test"), "d1.journal")
    db = MagicMock()
    db.info = {}
    db.query.return_value.filter.return_value.all.return_value = rows
    persistor.persist_readings(db, ALIAS, report)
    out: dict = {}
    for r in db.execute.call_args.args[1]:
        out.setdefault(r["channel_id"], []).append((r["timestamp"], r["value"]))
    return out


def test_a_declared_heat_call_channel_gets_no_pseudo_channel():
    assert heat_call_pseudo_names(WILLOW_013) == set()
    assert heat_call_pseudo_names(BEECH_011) == {
        "zone1-down-heat-call",
        "zone2-up-heat-call",
    }


def test_whitewire_readings_alone_synthesize_heat_call():
    whitewire = channel(
        WHITEWIRE, "W", Gw1Unit.enum_name(), GwChannelKind.DataChannel.value
    )
    heat_call = channel(
        HEAT_CALL, "Unitless", Gw1Unit.enum_name(), GwChannelKind.HeatCallSynth.value
    )
    by_channel = readings_by_channel([whitewire, heat_call], beech_report())
    threshold = ReportEventPersistor.whitewire_pwr_threshold_overrides[ALIAS]
    assert by_channel[heat_call.id] == [
        (ts, 1 if w > threshold else 0) for ts, w in by_channel[whitewire.id]
    ]


def test_a_report_carrying_heat_call_readings_gets_none_synthesized():
    whitewire = channel(
        WHITEWIRE, "W", Gw1Unit.enum_name(), GwChannelKind.DataChannel.value
    )
    heat_call = channel(
        HEAT_CALL, "Unitless", Gw1Unit.enum_name(), GwChannelKind.DerivedChannel.value
    )
    reported = {
        "ChannelName": HEAT_CALL,
        "ValueList": [1, 0],
        "ScadaReadTimeUnixMsList": [1760313600000, 1760313660000],
        "TypeName": "channel.readings",
        "Version": "002",
    }
    by_channel = readings_by_channel([whitewire, heat_call], beech_report([reported]))
    assert [v for _, v in by_channel[heat_call.id]] == [1, 0]
    assert len(by_channel[heat_call.id]) == 2
