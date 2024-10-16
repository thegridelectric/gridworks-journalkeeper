import copy

import pytest
from gjk.codec import pyd_to_sql, sql_to_pyd
from gjk.type_helpers import NodalHourlyEnergy


def test_nodal_energy():
    d = {
        "Id": "hp-odu-pwr_1706814000_hw1.isone.me.versant.keene.beech.ta",
        "HourStartS": 1706814000,
        "PowerChannel": {
            "Name": "hp-odu-pwr",
            "DisplayName": "HP ODU Power",
            "AboutNodeName": "hp-odu",
            "CapturedByNodeName": "primary-pwr-meter",
            "TelemetryName": "PowerW",
            "TerminalAssetAlias": "hw1.isone.me.versant.keene.beech.ta",
            "InPowerMetering": True,
            "StartS": 1704862800,
            "Id": "498da855-bac5-47e9-b83a-a11e56a50e67",
            "TypeName": "data.channel.gt",
            "Version": "001",
        },
        "WattHours": 1059,
    }

    e = NodalHourlyEnergy.from_dict(d)
    e_sql = pyd_to_sql(e)
    assert sql_to_pyd(e_sql) == e
    assert pyd_to_sql(sql_to_pyd(e_sql)).to_dict() == e_sql.to_dict()

    d2 = copy.deepcopy(d)
    d2["WattHours"] = -150
    with pytest.raises(ValueError):
        NodalHourlyEnergy(**d2)
