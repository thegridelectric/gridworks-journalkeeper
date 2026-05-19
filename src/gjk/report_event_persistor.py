import hashlib
import uuid
from datetime import datetime, timezone
from typing import List

from gw_data.db.models import ReadingChannelSql, ReadingSql
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from gjk.message_persistence_info import MessagePersistenceInfo
from gjk.pseudo_channels import PseudoChannel, register_pseudo_channels
from gjk.sema.enums import (
    Gw1LcTopState,
    Gw1LeafAllyAllTanksState,
    Gw1LeafAllyBufferOnlyState,
    Gw1LocalControlAllTanksState,
    Gw1LocalControlBufferOnlyState,
    Gw1LocalControlStandbyTopState,
    Gw1MainAutoState,
)
from gjk.sema.enums.gw_str_enum import SemaEnum
from gjk.sema.types import ReportEvent
from gjk.sema.types.old_versions.report_event_002 import ReportEvent002


class SemaEnumPseudoChannel(PseudoChannel):
    def __init__(self, name: str, display_name: str, enum_type: type[SemaEnum]):
        super().__init__(
            name, display_name, unit="Enum", unit_type=enum_type.enum_name()
        )
        self.enum_type = enum_type


class ReportEventPersistor:
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
            SemaEnumPseudoChannel(
                name="local-control-standby-state",
                display_name="Local Control Standby State",
                enum_type=Gw1LocalControlStandbyTopState,
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

    @classmethod
    def get_pseudo_channels(cls) -> list[PseudoChannel]:
        return [item for sublist in cls.STATE_CHANNELS.values() for item in sublist]

    def __init__(self, logger):
        self.logger = logger
        self.target_message_type = "report.event"
        self.enum_type_cache = {}

    def get_sema_enum_value(self, enum_type: type[SemaEnum], value_str: str) -> int:
        if value_str in enum_type.values():
            return enum_type.values().index(value_str)
        else:
            hash_object = hashlib.sha256(value_str.encode())
            hash_result = int(hash_object.hexdigest(), 16)
            self.logger.warn(
                f"Unrecognized enum value {value_str} in {enum_type.enum_name()} -- using hash value {hash_result} as default."
            )
            return hash_result

    def persist_readings(
        self, db: Session, from_alias: str, reportEvent: ReportEvent | ReportEvent002
    ):
        from_terminal_asset_alias = from_alias.split(".scada")[0] + ".ta"
        db_channels = (
            db.query(ReadingChannelSql)
            .filter(
                ReadingChannelSql.deactivated_date.is_(None),
                ReadingChannelSql.terminal_asset_alias == from_terminal_asset_alias,
            )
            .all()
        )

        message_id = uuid.UUID(reportEvent.message_id)

        db_channel_ids_by_name = {c.name: c.id for c in db_channels}
        readings: list[ReadingSql] = []
        for ch_readings in reportEvent.report.channel_reading_list:
            db_channel_id = db_channel_ids_by_name.get(ch_readings.channel_name)
            if db_channel_id is None:
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

        for states in reportEvent.report.state_list:
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
                        if db_channel_id is not None:
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

        dicts = [r.__dict__ for r in readings]
        if len(dicts) > 0:
            stmt = insert(ReadingSql).on_conflict_do_nothing(
                index_elements=["timestamp", "channel_id"]
            )
            db.execute(stmt, dicts)

    def persist_v002(self, from_alias: str, report: ReportEvent002):
        return MessagePersistenceInfo(
            id=report.message_id,
            created_at=datetime.fromtimestamp(report.time_created_ms / 1000),
            additional_db_operations=lambda db: self.persist_readings(
                db, from_alias, report
            ),
        )

    def persist_v003(self, from_alias: str, report: ReportEvent):
        return MessagePersistenceInfo(
            id=report.message_id,
            created_at=datetime.fromtimestamp(report.time_created_ms / 1000),
            additional_db_operations=lambda db: self.persist_readings(
                db, from_alias, report
            ),
        )


register_pseudo_channels(ReportEventPersistor.get_pseudo_channels())
