"""A layout.lite 013 declares the machines its scada hosts (StateMachines:
hosting node, enum, version). The journal derives one enum pseudo channel
per declared machine from the declaration, in place of the handle map a
house on an older layout still uses, and projects a report's machine
states into the channel of the hosting node, the handle's last segment.
Hermetic, no DB."""

import json
import logging
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import yaml

from gw_data.db.models import ReadingChannelSql

from gjk.house_status_projection import HouseStatusProjection
from gjk.layout_lite_persistor import LayoutLitePersistor
from gjk.pseudo_channels import layout_created_ms
from gjk.report_event_persistor import ENUMS_BY_NAME_AND_VERSION, ReportEventPersistor
from gjk.sema import SemaCodec
from gjk.sema.enums import (
    AquastatControlState,
    Gw1LcTopState,
    Gw1LeafAllyAllTanksState,
    Gw1LocalControlAllTanksState,
    Gw1MainAutoState,
    Gw2LcTopState,
    GwTopState,
    SinglePicoState,
)
from gjk.sema.types import GwStateMachine, LayoutLite
from gjk.sema.types.old_versions.layout_lite_012 import LayoutLite012

SAMPLES = Path(__file__).parent / "data" / "sample_messages"
# Real emissions of two simulated houses booted on jm/spruce-unlimbo
# (scada e38efebe), one per layout family.
WILLOW_013 = SAMPLES / "ops392" / "willow1-layout.lite-013-2026-10-22.json"
NOLAN_013 = SAMPLES / "ops392" / "spruce-sim-layout.lite-013-2026-10-22.json"
BEECH_011 = SAMPLES / "ops498" / "beech-layout.lite-011-2026-07-25.json"
BEECH_REPORT = SAMPLES / "ops498" / "beech-report.event-002-2025-10-13.json"
TA = "hw1.isone.me.versant.keene.beech.ta"
ALIAS = "hw1.isone.me.versant.keene.beech.scada"


ENUMS_BY_NAME_AND_VERSION_NAMES = {name for name, _ in ENUMS_BY_NAME_AND_VERSION}


def layout(path: Path):
    return SemaCodec().from_dict(json.loads(path.read_text()), auto_upgrade=False)


def report_with(state_rows: list[dict]):
    d = json.loads(BEECH_REPORT.read_text())
    d["Report"]["StateList"] = [
        {"TypeName": "machine.states", "Version": "000", **row} for row in state_rows
    ]
    return SemaCodec().from_dict(d, auto_upgrade=False)


def channel(name: str, enum_type) -> ReadingChannelSql:
    """A row as a 013 layout sync makes it: the enum name and version."""
    return ReadingChannelSql(
        id=uuid.uuid4(),
        name=name,
        terminal_asset_alias=TA,
        display_name=name,
        unit=enum_type.enum_version(),
        unit_type=enum_type.enum_name(),
        channel_type="gjk.pseudo",
        deactivated_date=None,
    )


def persist(
    rows: list[ReadingChannelSql], report
) -> tuple[ReportEventPersistor, MagicMock]:
    persistor = ReportEventPersistor(logging.getLogger("test"), "d1.journal")
    db = MagicMock()
    db.info = {}
    db.query.return_value.filter.return_value.all.return_value = rows
    persistor.persist_readings(db, ALIAS, report)
    return persistor, db


def test_both_families_decode_as_013():
    for path in (WILLOW_013, NOLAN_013):
        decoded = layout(path)
        assert isinstance(decoded, LayoutLite)
        assert decoded.state_machines
    assert isinstance(layout(BEECH_011).__class__, type)


def test_every_declared_machine_gets_one_channel_typed_by_its_enum():
    lite = layout(WILLOW_013)
    by_name = {pc.name: pc for pc in ReportEventPersistor.get_pseudo_channels(lite)}
    declared = {
        m.node_name: (m.state_enum, m.state_enum_version) for m in lite.state_machines
    }
    for node, (enum_name, version) in declared.items():
        name = ReportEventPersistor.declared_state_channel_name(node, enum_name)
        assert by_name[name].unit == version
        assert by_name[name].unit_type == enum_name
        assert (
            by_name[name].enum_type is ENUMS_BY_NAME_AND_VERSION[(enum_name, version)]
        )
    # One channel per machine, and nothing from the handle map.
    state_channels = [
        pc for pc in by_name.values() if pc.unit_type in ENUMS_BY_NAME_AND_VERSION_NAMES
    ]
    assert len(state_channels) == len(lite.state_machines)
    assert "local-control-buffer-only-state" not in by_name


def test_channel_names_continue_the_old_stream_and_follow_the_node_otherwise():
    name = ReportEventPersistor.declared_state_channel_name
    assert name("auto", Gw1MainAutoState.enum_name()) == "top-state"
    assert name("lc", Gw2LcTopState.enum_name()) == "local-control-top-state"
    assert (
        name("n", Gw1LocalControlAllTanksState.enum_name())
        == "local-control-all-tanks-state"
    )
    assert name("la", Gw1LeafAllyAllTanksState.enum_name()) == "ltn-all-tanks-state"
    assert name("buffer", SinglePicoState.enum_name()) == "buffer-pico-state"
    assert name("s", GwTopState.enum_name()) == "s-state"
    assert (
        name("aquastat-ctrl-relay", AquastatControlState.enum_name())
        == "aquastat-ctrl-relay-state"
    )


def test_a_machine_whose_enum_version_the_snapshot_lacks_gets_no_channel():
    machine = GwStateMachine(
        node_name="relay9", state_enum="not.a.vendored.enum", state_enum_version="000"
    )
    assert ReportEventPersistor.declared_state_channel(machine) is None
    newer = GwStateMachine(
        node_name="s", state_enum=GwTopState.enum_name(), state_enum_version="999"
    )
    assert ReportEventPersistor.declared_state_channel(newer) is None
    ReportEventPersistor.unvendored_machines.clear()
    lite = layout(WILLOW_013)
    lite.state_machines.append(newer)
    ReportEventPersistor.get_pseudo_channels(lite)
    [(_, enum_name, version)] = ReportEventPersistor.unvendored_machines
    assert (enum_name, version) == (GwTopState.enum_name(), "999")


def test_an_older_layout_keeps_the_handle_map():
    names = {
        pc.name for pc in ReportEventPersistor.get_pseudo_channels(layout(BEECH_011))
    }
    assert {"top-state", "local-control-top-state", "ltn-all-tanks-state"} <= names


def test_state_rows_project_into_the_hosting_node_channel():
    aquastat = channel("aquastat-ctrl-relay-state", AquastatControlState)
    top = channel("s-state", GwTopState)
    persistor, db = persist(
        [aquastat, top],
        report_with([
            {
                "MachineHandle": "auto.lc.n.aquastat-ctrl-relay",
                "StateEnum": AquastatControlState.enum_name(),
                "StateList": ["Boiler", "Scada"],
                "UnixMsList": [1760313900000, 1760313960000],
            },
            {
                "MachineHandle": "s",
                "StateEnum": GwTopState.enum_name(),
                "StateList": ["Admin"],
                "UnixMsList": [1760313900000],
            },
        ]),
    )
    rows = db.execute.call_args.args[1]
    by_channel = {}
    for r in rows:
        by_channel.setdefault(r["channel_id"], []).append(r["value"])
    assert by_channel[aquastat.id] == [
        AquastatControlState.values().index("Boiler"),
        AquastatControlState.values().index("Scada"),
    ]
    assert by_channel[top.id] == [GwTopState.values().index("Admin")]
    assert persistor.refused_states == {}


def test_a_node_channel_of_another_enum_is_not_written():
    # The channel row's unit_type is the declared enum; a row that names a
    # different enum for the same node is left to the handle map (which has
    # no entry) and tallied nowhere but the log.
    lc = channel("local-control-top-state", Gw1LcTopState)
    _, db = persist(
        [lc],
        report_with([
            {
                "MachineHandle": "auto.lc",
                "StateEnum": Gw2LcTopState.enum_name(),
                "StateList": ["Normal"],
                "UnixMsList": [1760313900000],
            }
        ]),
    )
    db.execute.assert_not_called()


def test_013_persistence_info_takes_created_ms_and_derives_no_status():
    lite = layout(WILLOW_013)
    assert isinstance(lite, LayoutLite)
    house_status = MagicMock(spec=HouseStatusProjection)
    persistor = LayoutLitePersistor(logging.getLogger("test"), house_status)
    info = persistor.persist_v013(ALIAS, None, lite)
    assert info.id == lite.message_id
    assert (
        info.created_at.timestamp() * 1000 == layout_created_ms(lite) == lite.created_ms
    )
    db = MagicMock()
    persistor.layouts = MagicMock()
    info.live_only_db_operations(db)
    persistor.layouts.project.assert_called_once()
    house_status.derive.assert_not_called()


def test_012_still_derives_a_status():
    example = yaml.safe_load(
        Path("src/gjk/sema/definitions/types/layout.lite/012.yaml").read_text()
    )["examples"][0]
    lite = SemaCodec().from_dict(json.loads(example), auto_upgrade=False)
    assert isinstance(lite, LayoutLite012)
    house_status = MagicMock(spec=HouseStatusProjection)
    persistor = LayoutLitePersistor(logging.getLogger("test"), house_status)
    persistor.layouts = MagicMock()
    persistor.persist_v012(ALIAS, None, lite).live_only_db_operations(MagicMock())
    house_status.derive.assert_called_once()
