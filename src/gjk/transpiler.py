from typing import Union

from gjk.models import (
    DataChannelSql,
    MessageSql,
    NodalHourlyEnergySql,
    ReadingSql,
    ScadaSql,
)
from gjk.type_helpers import Message, NodalHourlyEnergy, Reading, Scada
from gjk.types import DataChannelGt


def to_sql(
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


def to_pydantic(
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
