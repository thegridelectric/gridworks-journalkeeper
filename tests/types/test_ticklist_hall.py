"""Tests ticklist.hall type, version 101"""

from gjk.named_types import TicklistHall


def test_ticklist_hall_generated() -> None:
    d = {
        "HwUid": "pico_1fa376",
        "FirstTickTimestampNanoSecond": 1730120485296209000,
        "RelativeMicrosecondList": [1730120513626650],
        "PicoBeforePostTimestampNanoSecond": 1730120522058825000,
        "TypeName": "ticklist.hall",
        "Version": "101",
    }

    assert TicklistHall.from_dict(d).to_dict() == d
