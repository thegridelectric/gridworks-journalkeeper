from typing import Union

from gjk.models import DataChannelSql, NodalHourlyEnergySql, ReadingSql, ScadaSql
from gjk.type_helpers import NodalHourlyEnergy, Reading, Scada
from gjk.types import DataChannelGt


def to_sql(t:  Union[
        DataChannelGt,
        NodalHourlyEnergy,
        Reading,
        Scada]) -> Union[
                    DataChannelSql,
                    NodalHourlyEnergySql,
                    ReadingSql,
                    ScadaSql]:
    d = t.model_dump()
    d.pop('type_name', None)
    d.pop('version', None)
    if isinstance(t, DataChannelGt):
        return DataChannelSql(**d)
    elif isinstance(t, Reading):
        return ReadingSql(**t.model_dump())
    else:
        raise TypeError(f"Unsupported type: {type(t)}")

def to_pydantic(t: Union[
                    DataChannelSql,
                    NodalHourlyEnergySql,
                    ReadingSql,
                    ScadaSql]) -> Union[
                                    DataChannelGt,
                                    NodalHourlyEnergy,
                                    Reading,
                                    Scada]:
    if isinstance(t, DataChannelSql):
        return DataChannelGt(t.to_dict())
    elif isinstance(t, NodalHourlyEnergySql):
        return NodalHourlyEnergy(t.to_dict())
    elif isinstance(t, ReadingSql):
        return Reading(t.to_dict())
    elif isinstance(t, ScadaSql):
        return Scada(t.to_dict())
    else:
        raise TypeError(f"Unsupported type: {type(t)}")

