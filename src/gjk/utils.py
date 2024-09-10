import uuid
from typing import Any, Union

import pendulum
from pydantic import BaseModel

from gjk.models import (
    DataChannelSql,
    MessageSql,
    NodalHourlyEnergySql,
    ReadingSql,
    ScadaSql,
)
from gjk.type_helpers import Message, NodalHourlyEnergy, Reading, Scada
from gjk.types import BatchedReadings, DataChannelGt, GridworksEventGtShStatus


class FileNameMeta(BaseModel):
    from_alias: str
    type_name: str
    message_persisted_ms: int
    file_name: str


def type_to_sql(
    t: Union[DataChannelGt, Message, NodalHourlyEnergy, Reading, Scada],
) -> Union[DataChannelSql, MessageSql, NodalHourlyEnergySql, ReadingSql, ScadaSql]:
    d = t.to_sql_dict()

    d.pop("type_name", None)
    d.pop("version", None)
    if isinstance(t, DataChannelGt):
        return DataChannelSql(**d)
    elif isinstance(t, Message):
        return MessageSql(**d)
    elif isinstance(t, NodalHourlyEnergy):
        d["power_channel"] = DataChannelSql(**d["power_channel"])
        return NodalHourlyEnergySql(**d)
    elif isinstance(t, Reading):
        d["data_channel"] = DataChannelSql(**d["data_channel"])
        return ReadingSql(**d)
    elif isinstance(t, Scada):
        return ScadaSql(**d)
    else:
        raise TypeError(f"Unsupported type: {type(t)}")


def sql_to_type(
    t: Union[DataChannelSql, MessageSql, NodalHourlyEnergySql, ReadingSql, ScadaSql],
) -> Union[DataChannelGt, Message, NodalHourlyEnergy, Reading, Scada]:
    d = t.to_dict()
    if isinstance(t, DataChannelSql):
        return DataChannelGt(**d)
    elif isinstance(t, MessageSql):
        return MessageSql(**d)
    elif isinstance(t, NodalHourlyEnergySql):
        return NodalHourlyEnergy(**d)
    elif isinstance(t, ReadingSql):
        return Reading(**d)
    elif isinstance(t, ScadaSql):
        return Scada(**d)
    else:
        raise TypeError(f"Unsupported type: {type(t)}")


def type_to_msg(t: Any, fn: FileNameMeta)-> Message:
    if isinstance(t, BatchedReadings):
        if t.data_channel_list == []:
            return None
        else:
            try:
                return Message(
                    message_id=t.id,
                    from_alias=t.from_g_node_alias,
                    message_persisted_ms=fn.message_persisted_ms,
                    payload=t.to_dict(),
                    type_name=t.type_name,
                    message_created_ms=t.message_created_ms,
                )
            except Exception as e:
                print(f"Problem with {fn}: {e}")
                return None
    elif isinstance(t, GridworksEventGtShStatus):
        try:
            return Message(
                message_id=t.status.status_uid,
                from_alias=t.status.from_g_node_alias,
                message_persisted_ms=fn.message_persisted_ms,
                payload=t.to_dict(),
                type_name=t.type_name,
                message_created_ms=int(t.time_n_s / 10**6),
            )
        except Exception as e:
            print(f"Problem with {fn}: {e}")
            return None
    else:
        try:
            return Message(
                message_id=str(uuid.uuid4()),
                from_alias=fn.from_alias,
                type_name=t.type_name,
                message_persisted_ms=fn.message_persisted_ms,
                payload=t.to_dict(),
                message_created_ms=None,
            )
        except Exception as e:
            print(f"Problem with {fn}: {e}")
            return None


def str_from_ms(epoch_milli_seconds: int) -> str:
    return (
        pendulum.from_timestamp(epoch_milli_seconds / 1000)
        .in_timezone("America/New_York")
        .format("YYYY-MM-DD HH:mm:ss.SSS")
        + " America/NY"
    )
