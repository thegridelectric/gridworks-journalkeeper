import pendulum
from typing import Optional
from gjk.type_helpers import Message
from pydantic import BaseModel
import uuid
from gjk.named_types import (
    HeartbeatA,
    KeyparamChangeLog,
    PowerWatts,
    Report,
)
from gjk.old_types import BatchedReadings, GridworksEventGtShStatus

class FileNameMeta(BaseModel):
    from_alias: str
    type_name: str
    message_persisted_ms: int
    file_name: str


def str_from_ms(epoch_milli_seconds: int) -> str:
    return (
        pendulum.from_timestamp(epoch_milli_seconds / 1000)
        .in_timezone("America/New_York")
        .format("YYYY-MM-DD HH:mm:ss.SSS")
        + " America/NY"
    )

def tuple_to_msg(t: HeartbeatA, fn: FileNameMeta) -> Optional[Message]:
    """
    Take a tuple along with the meta data from the filename
    in the persistent store and return the Message to be put in the messages table
    of the journaldb.

    If the tuple is a BatchedReadings message with no actual readings, returns None
    If the tuple is not in the list of messages we are tracking in journaldb, also
    returns None
    """
    if isinstance(t, Report):
        return gridworks_event_report_to_msg(t, fn)
    elif isinstance(t, BatchedReadings):
        return batchedreading_to_msg(t, fn)
    elif isinstance(t, PowerWatts):
        return basic_to_msg(t, fn)
    elif isinstance(t, KeyparamChangeLog):
        return basic_to_msg(t, fn)
    elif isinstance(t, GridworksEventGtShStatus):
        return gridworkseventgtshstatus_to_msg(t, fn)
    else:
        return None


def gridworks_event_report_to_msg(
    t: GridworksEventReport, fn: FileNameMeta
) -> Optional[Message]:
    if (
        t.report.channel_reading_list == []
        and t.report.fsm_action_list == []
        and t.report.fsm_report_list == []
    ):
        return None
    else:
        return Message(
            message_id=t.report.id,
            from_alias=t.report.from_g_node_alias,
            message_persisted_ms=fn.message_persisted_ms,
            payload=t.report.to_dict(),
            message_type_name=t.report.type_name,
            message_created_ms=t.report.message_created_ms,
        )


def batchedreading_to_msg(t: BatchedReadings, fn: FileNameMeta) -> Optional[Message]:
    if t.data_channel_list == []:
        return None
    else:
        return Message(
            message_id=t.id,
            from_alias=t.from_g_node_alias,
            message_persisted_ms=fn.message_persisted_ms,
            payload=t.to_dict(),
            message_type_name=t.type_name,
            message_created_ms=t.message_created_ms,
        )


def gridworkseventgtshstatus_to_msg(
    t: GridworksEventGtShStatus, fn: FileNameMeta
) -> Optional[Message]:
    return Message(
        message_id=t.status.status_uid,
        from_alias=t.status.from_g_node_alias,
        message_persisted_ms=fn.message_persisted_ms,
        payload=t.to_dict(),
        message_type_name=t.type_name,
        message_created_ms=int(t.time_n_s / 10**6),
    )

def report_to_msg(
    t: Report, fn: FileNameMeta
) -> Optional[Message]:
    return Message(
        message_id=t.id,
        from_alias=t.from_g_node_alias,
        message_persisted_ms=fn.message_persisted_ms,
        payload=t.to_dict(),
        message_type_name=t.type_name,
        message_created_ms=t.message_created_ms,
    )


def basic_to_msg(t: HeartbeatA, fn: FileNameMeta) -> Message:
    return Message(
        message_id=str(uuid.uuid4()),
        from_alias=fn.from_alias,
        message_type_name=t.type_name,
        message_persisted_ms=fn.message_persisted_ms,
        payload=t.to_dict(),
        message_created_ms=None,
    )
