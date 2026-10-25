import importlib
import pkgutil
import uuid
from collections import Counter
from datetime import UTC, date, datetime, timezone
from typing import NamedTuple

from gw_data.db.models import MessageSql, ReadingSql
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from gjk.channel_resolver import ChannelResolver, Resolution
from gjk.message_persistence_info import MessagePersistenceInfo, default_message_id
from gjk.reading_channel_eras import load_channel_rows
from gw_data.db.models import ReadingChannelSql

import gjk.sema.enums as sema_enums
import gjk.sema.enums.old_versions as old_enums
from gjk.pseudo_channels import (
    DERIVED_ERA_LAYOUTS,
    ModernLayout,
    PseudoChannel,
    register_pseudo_channel_factory,
)
from gjk.sema.enums import (
    Gw1ActorClass,
    Gw1LcTopState,
    Gw1LeafAllyAllTanksState,
    Gw1LeafAllyBufferOnlyState,
    Gw1LocalControlAllTanksState,
    Gw1LocalControlBufferOnlyState,
    Gw1MainAutoState,
    GwChannelKind,
    LogLevel,
    SinglePicoState,
)
from gjk.sema.enums.gw_str_enum import SemaEnum
from gjk.sema.types import Glitch, GwStateMachine, LayoutLite, ReportEvent
from gjk.sema.types.old_versions.report_001 import Report001
from gjk.sema.types.old_versions.report_event_000 import ReportEvent000
from gjk.sema.types.old_versions.report_event_002 import ReportEvent002
from gjk.sema.types.old_versions.report_event_003 import ReportEvent003
from gjk.zone_heat_call_pseudo_channel import ZoneHeatCallPseudoChannel

ReportEventType = ReportEvent | ReportEvent003 | ReportEvent002 | ReportEvent000


class SemaEnumPseudoChannel(PseudoChannel):
    """A channel whose readings are a machine's states, as positions in the
    enum's value list. `unit_type` is the enum name; `unit` is the enum
    version a 013 layout declares for the machine, or "Enum" for a channel
    the handle map names on an older layout, which declares no version."""

    def __init__(
        self,
        name: str,
        display_name: str,
        enum_type: type[SemaEnum],
        version: str | None = None,
    ):
        super().__init__(
            name,
            display_name,
            unit=version if version is not None else "Enum",
            unit_type=enum_type.enum_name(),
            kind=GwChannelKind.StateMachine,
        )
        self.enum_type = enum_type


def vendored_enums() -> list[type[SemaEnum]]:
    """Every enum the snapshot vendors: the current version of each and the
    old versions kept beside them."""
    modules = [sema_enums] + [
        importlib.import_module(f"{old_enums.__name__}.{m.name}")
        for m in pkgutil.iter_modules(old_enums.__path__)
    ]
    return [
        e
        for module in modules
        for e in vars(module).values()
        if isinstance(e, type)
        and issubclass(e, SemaEnum)
        and e is not SemaEnum
        and e.enum_name.__func__ is not SemaEnum.enum_name.__func__
    ]


# The current version of every vendored enum, by sema name: what the handle
# map's channels on a pre-013 layout are typed by.
ENUMS_BY_NAME: dict[str, type[SemaEnum]] = {
    e.enum_name(): e
    for e in vars(sema_enums).values()
    if isinstance(e, type)
    and issubclass(e, SemaEnum)
    and e is not SemaEnum
    and e.enum_name.__func__ is not SemaEnum.enum_name.__func__
}
# Every vendored enum by (name, version): what a 013 layout's StateMachines
# declaration resolves to.
ENUMS_BY_NAME_AND_VERSION: dict[tuple[str, str], type[SemaEnum]] = {
    (e.enum_name(), e.enum_version()): e for e in vendored_enums()
}


class MismatchKey(NamedTuple):
    """One disagreement between the layout in force and the journal: the row
    a channel name resolved to holds a `channel_id` other than the Id the
    layout declares for that name. In-process tally state, not durable data;
    the glitch it raises is the word."""

    terminal_asset_alias: str
    channel: str
    declared_id: uuid.UUID | None
    row_channel_id: uuid.UUID | None


# The node a journalkeeper glitch reports from.
GLITCH_NODE = "channel-resolver"


class ReportEventPersistor:
    # The channel names a house's state stream had before layout.lite 013
    # declared its machines (STATE_CHANNELS, by handle). A 013 house keeps
    # them for the same machines, by hosting node and enum, so the stream
    # continues across the roll; every other declared machine gets
    # `<node>-state`.
    CONTINUED_STATE_CHANNEL_NAMES: dict[tuple[str, str], str] = {
        ("auto", Gw1MainAutoState.enum_name()): "top-state",
        ("lc", Gw1LcTopState.enum_name()): "local-control-top-state",
        ("lc", sema_enums.Gw2LcTopState.enum_name()): "local-control-top-state",
        (
            "n",
            Gw1LocalControlAllTanksState.enum_name(),
        ): "local-control-all-tanks-state",
        (
            "n",
            Gw1LocalControlBufferOnlyState.enum_name(),
        ): "local-control-buffer-only-state",
        ("la", Gw1LeafAllyAllTanksState.enum_name()): "ltn-all-tanks-state",
        ("la", Gw1LeafAllyBufferOnlyState.enum_name()): "ltn-buffer-only-state",
    }
    STATE_CHANNEL_SUFFIX = "-state"
    # (terminal_asset_alias, enum, version) -> machines a layout declared
    # with an enum version the snapshot does not vendor: no channel, no
    # readings, until the snapshot is re-vendored. Read by the S3 importer's
    # run summary; shared by every instance since the factory is a classmethod.
    unvendored_machines: Counter[tuple[str, str, str]] = Counter()

    STATE_CHANNELS: dict[str, list[SemaEnumPseudoChannel]] = {
        "auto": [
            SemaEnumPseudoChannel(
                name="top-state", display_name="Top State", enum_type=Gw1MainAutoState
            )
        ],
        "auto.lc": [
            SemaEnumPseudoChannel(
                name="local-control-top-state",
                display_name="Local Control Top State",
                enum_type=Gw1LcTopState,
            )
        ],
        "auto.lc.n": [
            SemaEnumPseudoChannel(
                name="local-control-all-tanks-state",
                display_name="Local Control All Tanks State",
                enum_type=Gw1LocalControlAllTanksState,
            ),
            SemaEnumPseudoChannel(
                name="local-control-buffer-only-state",
                display_name="Local Control Buffer Only State",
                enum_type=Gw1LocalControlBufferOnlyState,
            ),
        ],
        "ltn.la": [
            SemaEnumPseudoChannel(
                name="ltn-all-tanks-state",
                display_name="LTN All Tanks State",
                enum_type=Gw1LeafAllyAllTanksState,
            ),
            SemaEnumPseudoChannel(
                name="ltn-buffer-only-state",
                display_name="LTN Buffer Only State",
                enum_type=Gw1LeafAllyBufferOnlyState,
            ),
        ],
    }

    # Actor classes whose node is backed by one pico. The pico-cycler reports
    # each pico's single.pico.state as a machine.states row keyed by that
    # node's handle; each such node gets one enum pseudo channel.
    PICO_ACTOR_CLASSES = {
        Gw1ActorClass.ApiTankModule,
        Gw1ActorClass.ApiFlowModule,
        Gw1ActorClass.ApiBtuMeter,
    }
    PICO_STATE_CHANNEL_SUFFIX = "-pico-state"

    @classmethod
    def pico_state_channel(cls, node_name: str) -> SemaEnumPseudoChannel:
        return SemaEnumPseudoChannel(
            name=f"{node_name}{cls.PICO_STATE_CHANNEL_SUFFIX}",
            display_name=f"{node_name} Pico State",
            enum_type=SinglePicoState,
        )

    @classmethod
    def declared_state_channel_name(cls, node_name: str, state_enum: str) -> str:
        if state_enum == SinglePicoState.enum_name():
            return f"{node_name}{cls.PICO_STATE_CHANNEL_SUFFIX}"
        return cls.CONTINUED_STATE_CHANNEL_NAMES.get(
            (node_name, state_enum), f"{node_name}{cls.STATE_CHANNEL_SUFFIX}"
        )

    @classmethod
    def declared_state_channel(
        cls, machine: GwStateMachine
    ) -> SemaEnumPseudoChannel | None:
        """One enum pseudo channel per machine a 013 layout declares, resolved
        to the vendored enum of the declared name and version. None when the
        snapshot lacks that version: the states stay in `messages` and
        nothing projects until the snapshot is re-vendored."""
        enum_type = ENUMS_BY_NAME_AND_VERSION.get((
            machine.state_enum,
            machine.state_enum_version,
        ))
        if enum_type is None:
            return None
        return SemaEnumPseudoChannel(
            name=cls.declared_state_channel_name(machine.node_name, machine.state_enum),
            display_name=f"{machine.node_name} {machine.state_enum}",
            enum_type=enum_type,
            version=machine.state_enum_version,
        )

    @classmethod
    def get_pseudo_channels(cls, layout: ModernLayout) -> list[PseudoChannel]:
        result: list[PseudoChannel] = []
        if isinstance(layout, LayoutLite):
            for machine in layout.state_machines:
                channel = cls.declared_state_channel(machine)
                if channel is None:
                    cls.unvendored_machines[
                        (
                            layout.from_g_node_alias.split(".scada")[0] + ".ta",
                            machine.state_enum,
                            machine.state_enum_version,
                        )
                    ] += 1
                    continue
                result.append(channel)
        else:
            result.extend(
                item for sublist in cls.STATE_CHANNELS.values() for item in sublist
            )
            for node in layout.sh_nodes:
                if node.actor_class in cls.PICO_ACTOR_CLASSES:
                    result.append(cls.pico_state_channel(node.name))

        # A heat-call channel the layout declares, as a DataChannel or a
        # DerivedChannel, is the scada's to report; the pseudo channel is
        # only for a house whose layout declares none.
        declared_names = {ch.name for ch in layout.data_channels}
        if isinstance(layout, DERIVED_ERA_LAYOUTS):
            declared_names |= {ch.name for ch in layout.derived_channels}
        for ch_name in declared_names:
            if "whitewire-pwr" in ch_name:
                heatcall_channel_name = ch_name.replace("whitewire-pwr", "heat-call")
                if heatcall_channel_name not in declared_names:
                    result.append(ZoneHeatCallPseudoChannel(heatcall_channel_name))

        return result

    def __init__(self, logger, service_alias: str):
        self.logger = logger
        # the alias a glitch of the journalkeeper's own is journaled under
        self.service_alias = service_alias
        self.target_message_type = "report.event"
        self.fanout_on_import = True  # history fan-out; replays welcome
        self.resolver = ChannelResolver(logger)
        # Load tallies, read by the S3 importer's run summary.
        # (terminal_asset_alias, channel name) -> readings with no channel row
        # for the report time.
        self.dropped_readings: Counter[tuple[str, str]] = Counter()
        # (enum name, value) -> state readings refused because the value is
        # not in the channel's enum version.
        self.refused_states: Counter[tuple[str, str]] = Counter()
        # readings routed to a row whose channel_id is not the Id the layout
        # in force declares for the name.
        self.channel_id_mismatches: Counter[MismatchKey] = Counter()
        # the keys the report being persisted mismatched on; read by the
        # live-only glitch step.
        self.mismatched_in_report: set[MismatchKey] = set()
        # key -> the UTC day its last glitch was journaled
        self.glitch_days: dict[MismatchKey, date] = {}
        self.db_channel_rows_by_id: dict[uuid.UUID, ReadingChannelSql] = {}

    def state_readings(
        self,
        enum_type: type[SemaEnum],
        channel_id: uuid.UUID,
        message_id: uuid.UUID,
        unix_ms_list: list[int],
        state_list: list[str],
    ) -> list[ReadingSql]:
        """A machine's states as readings: each value is the state's position
        in the enum's value list. A state the enum lacks is refused."""
        values = enum_type.values()
        readings: list[ReadingSql] = []
        for t_ms, state in zip(unix_ms_list, state_list, strict=True):
            if state not in values:
                self.logger.warn(
                    f"State {state} is not in {enum_type.enum_name()} {enum_type.enum_version()}: refused"
                )
                self.refused_states[(enum_type.enum_name(), state)] += 1
                continue
            readings.append(
                ReadingSql(
                    channel_id=channel_id,
                    message_id=message_id,
                    timestamp=datetime.fromtimestamp(t_ms / 1000, timezone.utc),
                    value=values.index(state),
                )
            )
        return readings

    def collect_channel_state_readings(
        self,
        readings: list[ReadingSql],
        reportEvent: ReportEventType,
        message_id: uuid.UUID,
        db_channel_ids_by_name: dict[str, uuid.UUID],
    ):
        if isinstance(reportEvent.report, Report001):
            # report:001 carries FsmActionList in place of StateList: no
            # machine states to project.
            return
        for states in reportEvent.report.state_list:
            if states.state_enum == SinglePicoState.enum_name():
                self.collect_pico_state_readings(
                    readings, states, reportEvent, message_id, db_channel_ids_by_name
                )
                continue
            if self.collect_declared_state_readings(
                readings, states, message_id, db_channel_ids_by_name
            ):
                continue
            machine_handle = (
                str(states.machine_handle)
                .replace("auto.h", "auto.lc")
                .replace("a.aa", "ltn.la")
            )
            state_channels = self.STATE_CHANNELS.get(machine_handle)

            if (
                "auto.lc." in machine_handle
                and "auto.lc.n" not in machine_handle
                and "relay" in machine_handle
            ):
                self.logger.warn(
                    f"Found auto.lc relay state: {machine_handle} (msg_id={message_id})"
                )

            if state_channels is not None:
                found_channel = False
                for channel in state_channels:
                    if channel.enum_type.enum_name() == states.state_enum:
                        found_channel = True
                        db_channel_id = db_channel_ids_by_name.get(channel.name)
                        if db_channel_id is None:
                            self.dropped_readings[
                                (self.terminal_asset_alias(reportEvent), channel.name)
                            ] += len(states.unix_ms_list)
                        else:
                            readings.extend(
                                self.state_readings(
                                    channel.enum_type,
                                    db_channel_id,
                                    message_id,
                                    states.unix_ms_list,
                                    states.state_list,
                                )
                            )
                        break

                if not found_channel:
                    self.logger.warn(
                        f"Unexpected enum {states.state_enum} found for state {states.machine_handle} (msg_id={message_id})"
                    )

    def collect_declared_state_readings(
        self,
        readings: list[ReadingSql],
        states,
        message_id: uuid.UUID,
        db_channel_ids_by_name: dict[str, uuid.UUID],
    ) -> bool:
        """Project a machine's states into the channel its 013 layout
        declared: the channel named for the hosting node (the handle's last
        segment) and typed by the row's enum and version. True when the row
        was taken. A house on an older layout has no such channel and falls
        through to the handle map."""
        node_name = str(states.machine_handle).split(".")[-1]
        channel_name = self.declared_state_channel_name(node_name, states.state_enum)
        db_channel_id = db_channel_ids_by_name.get(channel_name)
        if db_channel_id is None:
            return False
        row = self.db_channel_rows_by_id[db_channel_id]
        if row.unit_type != states.state_enum:
            return False
        enum_type = ENUMS_BY_NAME_AND_VERSION.get((row.unit_type, row.unit))
        if enum_type is None:
            return False
        readings.extend(
            self.state_readings(
                enum_type,
                db_channel_id,
                message_id,
                states.unix_ms_list,
                states.state_list,
            )
        )
        return True

    def collect_pico_state_readings(
        self,
        readings: list[ReadingSql],
        states,
        reportEvent: ReportEventType,
        message_id: uuid.UUID,
        db_channel_ids_by_name: dict[str, uuid.UUID],
    ):
        """A single.pico.state row is keyed by the pico-backed node's handle;
        its channel is named from the handle's last segment, the node name."""
        node_name = str(states.machine_handle).split(".")[-1]
        channel_name = f"{node_name}{self.PICO_STATE_CHANNEL_SUFFIX}"
        db_channel_id = db_channel_ids_by_name.get(channel_name)
        if db_channel_id is None:
            self.dropped_readings[
                (self.terminal_asset_alias(reportEvent), channel_name)
            ] += len(states.unix_ms_list)
            return
        readings.extend(
            self.state_readings(
                SinglePicoState,
                db_channel_id,
                message_id,
                states.unix_ms_list,
                states.state_list,
            )
        )

    whitewire_pwr_threshold_default = 20
    whitewire_pwr_threshold_overrides = {
        "hw1.isone.me.versant.keene.beech.scada": 100,
        "hw1.isone.me.versant.keene.elm.scada": 1,
    }

    def collect_zone_heat_call_readings(
        self,
        readings: list[ReadingSql],
        reportEvent: ReportEventType,
        message_id: uuid.UUID,
        db_channel_ids_by_name: dict[str, uuid.UUID],
    ):
        # A report that carries heat-call readings comes from a scada that
        # reports them itself; synthesis is only for a report without them.
        if any(
            "heat-call" in ch.channel_name
            for ch in reportEvent.report.channel_reading_list
        ):
            return
        threshold = self.whitewire_pwr_threshold_overrides.get(
            reportEvent.report.from_g_node_alias, self.whitewire_pwr_threshold_default
        )

        whitewire_pwr_channel_names_by_id = {
            id: name
            for name, id in db_channel_ids_by_name.items()
            if "whitewire-pwr" in name
        }
        # # Find all the whitewire-pwr readings, and add corresponding readings to heat-call
        for r in readings:
            whitewire_pwr_channel_name = whitewire_pwr_channel_names_by_id.get(
                r.channel_id
            )
            if whitewire_pwr_channel_name:
                heat_call_channel_id = db_channel_ids_by_name.get(
                    whitewire_pwr_channel_name.replace("whitewire-pwr", "heat-call")
                )
                if heat_call_channel_id:
                    readings.append(
                        ReadingSql(
                            channel_id=heat_call_channel_id,
                            message_id=message_id,
                            timestamp=r.timestamp,
                            value=1 if r.value > threshold else 0,
                        )
                    )

    @staticmethod
    def terminal_asset_alias(reportEvent: ReportEventType) -> str:
        return reportEvent.report.from_g_node_alias.split(".scada")[0] + ".ta"

    def persist_readings(
        self, db: Session, from_alias: str, reportEvent: ReportEventType
    ):
        from_terminal_asset_alias = from_alias.split(".scada")[0] + ".ta"
        report_time = datetime.fromtimestamp(reportEvent.time_created_ms / 1000, UTC)
        channel_rows = load_channel_rows(db, from_terminal_asset_alias)
        resolution = self.resolver.resolve(
            db, from_alias, from_terminal_asset_alias, channel_rows, report_time
        )
        db_channel_ids_by_name = resolution.row_ids
        self.db_channel_rows_by_id: dict[uuid.UUID, ReadingChannelSql] = {
            r.id: r for r in channel_rows
        }
        self.mismatched_in_report = set()

        message_id = uuid.UUID(reportEvent.message_id)

        readings: list[ReadingSql] = []
        for ch_readings in reportEvent.report.channel_reading_list:
            db_channel_id = db_channel_ids_by_name.get(ch_readings.channel_name)
            if db_channel_id is None:
                self.dropped_readings[
                    (from_terminal_asset_alias, ch_readings.channel_name)
                ] += len(ch_readings.value_list)
                continue
            else:
                self.check_channel_id(
                    from_terminal_asset_alias,
                    ch_readings.channel_name,
                    db_channel_id,
                    resolution,
                    len(ch_readings.value_list),
                )
                # Reports can duplicate the same timestamp and value, so we need to de-duplicate it.
                readings_by_ts = {}
                for ts, value in zip(
                    ch_readings.scada_read_time_unix_ms_list,
                    ch_readings.value_list,
                    strict=True,
                ):
                    if ts not in readings_by_ts:
                        readings_by_ts[ts] = ReadingSql(
                            channel_id=db_channel_id,
                            message_id=message_id,
                            timestamp=datetime.fromtimestamp(ts / 1000, timezone.utc),
                            value=value,
                        )

                readings.extend(readings_by_ts.values())

        self.collect_channel_state_readings(
            readings, reportEvent, message_id, db_channel_ids_by_name
        )
        self.collect_zone_heat_call_readings(
            readings, reportEvent, message_id, db_channel_ids_by_name
        )

        dicts = [r.__dict__ for r in readings]
        if len(dicts) > 0:
            stmt = insert(ReadingSql).on_conflict_do_nothing(
                index_elements=["timestamp", "channel_id"]
            )
            db.execute(stmt, dicts)

    def check_channel_id(
        self,
        terminal_asset_alias: str,
        name: str,
        row_id: uuid.UUID,
        resolution: Resolution,
        n_readings: int,
    ) -> None:
        """The row a name resolved to holds the Id the layout in force declares
        for it (none for a pseudo row). A disagreement is tallied, not
        refused: the readings are the row's, the bookkeeping is wrong."""
        if name not in resolution.declared_ids:
            return
        row = self.db_channel_rows_by_id[row_id]
        declared = resolution.declared_ids[name]
        if row.channel_id == declared:
            return
        key = MismatchKey(terminal_asset_alias, name, declared, row.channel_id)
        self.channel_id_mismatches[key] += n_readings
        self.mismatched_in_report.add(key)

    def journal_mismatch_glitches(self, db: Session, now: datetime) -> None:
        """One Warning glitch per mismatch key per UTC day, journaled under the
        journalkeeper's own alias so the alerter's reports see it. The count
        is the readings tallied under the key since this process started."""
        for i, key in enumerate(sorted(self.mismatched_in_report, key=str)):
            if self.glitch_days.get(key) == now.date():
                continue
            self.glitch_days[key] = now.date()
            created = datetime.fromtimestamp(
                int(now.timestamp() * 1000 + i) / 1000, tz=UTC
            )
            glitch = Glitch(
                from_g_node_alias=self.service_alias,
                node=GLITCH_NODE,
                type=LogLevel.Warning,
                summary=f"channel-id-mismatch {key.channel} at {key.terminal_asset_alias}",
                details=(
                    f"The layout in force declares {key.channel} with Id "
                    f"{key.declared_id}; the reading_channels row its readings go "
                    f"to holds channel_id {key.row_channel_id}. "
                    f"{self.channel_id_mismatches[key]} readings since the "
                    "journalkeeper started."
                ),
                created_ms=int(created.timestamp() * 1000),
            )
            msg = MessageSql(
                id=uuid.UUID(
                    default_message_id(self.service_alias, glitch.type_name, created)
                ),
                timestamp=created,
                created_at=created,
                persisted_at=now,
                from_alias=self.service_alias,
                message_type_name=glitch.type_name,
                payload=glitch.to_dict(),
            )
            stmt = insert(MessageSql).on_conflict_do_nothing(
                index_elements=["timestamp", "id"]
            )
            db.execute(stmt, [msg.__dict__])
            self.logger.warning(f"{glitch.summary}: {glitch.details}")

    def persist_v000(
        self, from_alias: str, time_received: datetime, report: ReportEvent000
    ):
        return MessagePersistenceInfo(
            id=report.message_id,
            created_at=datetime.fromtimestamp(report.time_created_ms / 1000, tz=UTC),
            additional_db_operations=lambda db: self.persist_readings(
                db, from_alias, report
            ),
            live_only_db_operations=lambda db: self.journal_mismatch_glitches(
                db, time_received
            ),
        )

    def persist_v002(
        self, from_alias: str, time_received: datetime, report: ReportEvent002
    ):
        return MessagePersistenceInfo(
            id=report.message_id,
            created_at=datetime.fromtimestamp(report.time_created_ms / 1000, tz=UTC),
            additional_db_operations=lambda db: self.persist_readings(
                db, from_alias, report
            ),
            live_only_db_operations=lambda db: self.journal_mismatch_glitches(
                db, time_received
            ),
        )

    def persist_v003(
        self, from_alias: str, time_received: datetime, report: ReportEvent003
    ):
        return MessagePersistenceInfo(
            id=report.message_id,
            created_at=datetime.fromtimestamp(report.time_created_ms / 1000, tz=UTC),
            additional_db_operations=lambda db: self.persist_readings(
                db, from_alias, report
            ),
            live_only_db_operations=lambda db: self.journal_mismatch_glitches(
                db, time_received
            ),
        )

    def persist_v004(
        self, from_alias: str, time_received: datetime, report: ReportEvent
    ):
        # 004 restores the propagation axioms, so message_id is Report.Id and
        # time_created_ms is Report.MessageCreatedMs by construction.
        return MessagePersistenceInfo(
            id=report.message_id,
            created_at=datetime.fromtimestamp(report.time_created_ms / 1000, tz=UTC),
            additional_db_operations=lambda db: self.persist_readings(
                db, from_alias, report
            ),
            live_only_db_operations=lambda db: self.journal_mismatch_glitches(
                db, time_received
            ),
        )


register_pseudo_channel_factory(ReportEventPersistor.get_pseudo_channels)
