"""The pico-cycler reports each pico's single.pico.state as a machine.states
row keyed by the pico-backed node's handle. The journal gives every
pico-backed node (tank module, flow module, BTU meter) one enum pseudo
channel, `<node>-pico-state`, and projects the rows into it. Hermetic, no DB."""

import json
import logging
import uuid
from pathlib import Path
from unittest.mock import MagicMock

from gw_data.db.models import ReadingChannelSql

from gjk.report_event_persistor import ReportEventPersistor
from gjk.sema import SemaCodec
from gjk.sema.enums import SinglePicoState

SAMPLES = Path(__file__).parent / "data" / "sample_messages" / "ops498"
ALIAS = "hw1.isone.me.versant.keene.beech.scada"
TA = "hw1.isone.me.versant.keene.beech.ta"


def _layout():
    return SemaCodec().from_dict(
        json.loads((SAMPLES / "beech-layout.lite-011-2026-07-25.json").read_text()),
        auto_upgrade=False,
    )


def _report_with_pico_rows():
    d = json.loads((SAMPLES / "beech-report.event-002-2025-10-13.json").read_text())
    d["Report"]["StateList"].append({
        "MachineHandle": "buffer",
        "StateEnum": "single.pico.state",
        "StateList": ["Flatlined", "Zombie"],
        "UnixMsList": [1760313900000, 1760313960000],
        "TypeName": "machine.states",
        "Version": "000",
    })
    return SemaCodec().from_dict(d, auto_upgrade=False)


def _channel(name):
    return ReadingChannelSql(
        id=uuid.uuid4(),
        name=name,
        terminal_asset_alias=TA,
        display_name=name,
        unit="Enum",
        unit_type=SinglePicoState.enum_name(),
        channel_type="c",
        deactivated_date=None,
    )


def test_every_pico_backed_node_gets_a_state_channel():
    names = {pc.name: pc for pc in ReportEventPersistor.get_pseudo_channels(_layout())}
    for node in ("buffer", "tank1", "tank2", "tank3", "sieg-flow", "primary-btu"):
        pc = names[f"{node}-pico-state"]
        assert pc.unit_type == SinglePicoState.enum_name()
    assert "top-state" in names


def test_pico_rows_without_a_channel_are_tallied_as_dropped():
    persistor = ReportEventPersistor(logging.getLogger("test"))
    db = MagicMock()
    db.info = {}
    db.query.return_value.filter.return_value.all.return_value = []
    persistor.persist_readings(db, ALIAS, _report_with_pico_rows())
    assert persistor.dropped_readings[(TA, "buffer-pico-state")] == 2
    db.execute.assert_not_called()


def test_pico_rows_project_into_the_node_channel_as_enum_indexes():
    persistor = ReportEventPersistor(logging.getLogger("test"))
    channel = _channel("buffer-pico-state")
    db = MagicMock()
    db.info = {}
    db.query.return_value.filter.return_value.all.return_value = [channel]
    persistor.persist_readings(db, ALIAS, _report_with_pico_rows())
    db.execute.assert_called_once()
    rows = [r for r in db.execute.call_args.args[1] if r["channel_id"] == channel.id]
    assert [r["value"] for r in rows] == [
        SinglePicoState.values().index("Flatlined"),
        SinglePicoState.values().index("Zombie"),
    ]
    assert persistor.enum_fallbacks == {}
