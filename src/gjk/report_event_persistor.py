import hashlib
import uuid
from collections import Counter
from datetime import UTC, datetime, timezone

from gw_data.db.models import ReadingSql
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from gjk.message_persistence_info import MessagePersistenceInfo
from gjk.reading_channel_eras import channel_ids_at, load_channel_rows
from gw_data.db.models import ReadingChannelSql

import gjk.sema.enums as sema_enums
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
    SinglePicoState,
)
from gjk.sema.enums.gw_str_enum import SemaEnum
from gjk.sema.types import GwStateMachine, LayoutLite, ReportEvent
from gjk.sema.types.old_versions.report_001 import Report001
from gjk.sema.types.old_versions.report_event_000 import ReportEvent000
from gjk.sema.types.old_versions.report_event_002 import ReportEvent002
from gjk.sema.types.old_versions.report_event_003 import ReportEvent003
from gjk.zone_heat_call_pseudo_channel import ZoneHeatCallPseudoChannel

ReportEventType = ReportEvent | ReportEvent003 | ReportEvent002 | ReportEvent000


class SemaEnumPseudoChannel(PseudoChannel):
    def __init__(self, name: str, display_name: str, enum_type: type[SemaEnum]):
        super().__init__(
            name, display_name, unit="Enum", unit_type=enum_type.enum_name()
        )
        self.enum_type = enum_type


# Every enum the snapshot vendors, by its sema name: what a layout's
# StateMachines declaration resolves to.
ENUMS_BY_NAME: dict[str, type[SemaEnum]] = {
    e.enum_name(): e
    for e in vars(sema_enums).values()
    if isinstance(e, type)
    and issubclass(e, SemaEnum)
    and e is not SemaEnum
    and e.enum_name.__func__ is not SemaEnum.enum_name.__func__
}


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
        to the vendored enum of the declared name. None when the snapshot
        lacks the enum: the states stay in `messages` and nothing projects."""
        enum_type = ENUMS_BY_NAME.get(machine.state_enum)
        if enum_type is None:
            return None
        return SemaEnumPseudoChannel(
            name=cls.declared_state_channel_name(machine.node_name, machine.state_enum),
            display_name=f"{machine.node_name} {machine.state_enum}",
            enum_type=enum_type,
        )

    @classmethod
    def get_pseudo_channels(cls, layout: ModernLayout) -> list[PseudoChannel]:
        result: list[PseudoChannel] = []
        if isinstance(layout, LayoutLite):
            for machine in layout.state_machines:
                channel = cls.declared_state_channel(machine)
                if channel is not None:
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

    def __init__(self, logger):
        self.logger = logger
        self.target_message_type = "report.event"
        self.fanout_on_import = True  # history fan-out; replays welcome
        self.enum_type_cache = {}
        # Load tallies, read by the S3 importer's run summary.
        # (terminal_asset_alias, channel name) -> readings with no channel row
        # whose era contains the report time.
        self.dropped_readings: Counter[tuple[str, str]] = Counter()
        # (enum name, value) -> state readings stored under the sha256
        # fallback because the value is not in the vendored enum.
        self.enum_fallbacks: Counter[tuple[str, str]] = Counter()
        self.db_channel_rows_by_id: dict[uuid.UUID, ReadingChannelSql] = {}

    def get_sema_enum_value(self, enum_type: type[SemaEnum], value_str: str) -> int:
        if value_str in enum_type.values():
            return enum_type.values().index(value_str)
        else:
            hash_object = hashlib.sha256(value_str.encode())
            hash_result = int(hash_object.hexdigest(), 16)
            self.logger.warn(
                f"Unrecognized enum value {value_str} in {enum_type.enum_name()} -- using hash value {hash_result} as default."
            )
            self.enum_fallbacks[(enum_type.enum_name(), value_str)] += 1
            return hash_result

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
                                map(
                                    lambda t_s: ReadingSql(
                                        channel_id=db_channel_id,
                                        message_id=message_id,
                                        timestamp=datetime.fromtimestamp(
                                            t_s[0] / 1000, timezone.utc
                                        ),
                                        value=self.get_sema_enum_value(
                                            channel.enum_type, t_s[1]
                                        ),
                                    ),
                                    zip(states.unix_ms_list, states.state_list),
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
        segment) and typed by the row's enum. True when the row was taken.
        A house on an older layout has no such channel and falls through to
        the handle map."""
        node_name = str(states.machine_handle).split(".")[-1]
        channel_name = self.declared_state_channel_name(node_name, states.state_enum)
        db_channel_id = db_channel_ids_by_name.get(channel_name)
        if db_channel_id is None:
            return False
        row = self.db_channel_rows_by_id[db_channel_id]
        if row.unit_type != states.state_enum:
            return False
        enum_type = ENUMS_BY_NAME.get(states.state_enum)
        if enum_type is None:
            return False
        readings.extend(
            ReadingSql(
                channel_id=db_channel_id,
                message_id=message_id,
                timestamp=datetime.fromtimestamp(t_ms / 1000, timezone.utc),
                value=self.get_sema_enum_value(enum_type, state),
            )
            for t_ms, state in zip(states.unix_ms_list, states.state_list, strict=True)
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
            ReadingSql(
                channel_id=db_channel_id,
                message_id=message_id,
                timestamp=datetime.fromtimestamp(t_ms / 1000, timezone.utc),
                value=self.get_sema_enum_value(SinglePicoState, state),
            )
            for t_ms, state in zip(states.unix_ms_list, states.state_list, strict=True)
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
        db_channel_ids_by_name = channel_ids_at(channel_rows, report_time)
        self.db_channel_rows_by_id: dict[uuid.UUID, ReadingChannelSql] = {
            r.id: r for r in channel_rows
        }

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

    def persist_v000(
        self, from_alias: str, time_received: datetime, report: ReportEvent000
    ):
        return MessagePersistenceInfo(
            id=report.message_id,
            created_at=datetime.fromtimestamp(report.time_created_ms / 1000, tz=UTC),
            additional_db_operations=lambda db: self.persist_readings(
                db, from_alias, report
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
        )


register_pseudo_channel_factory(ReportEventPersistor.get_pseudo_channels)
