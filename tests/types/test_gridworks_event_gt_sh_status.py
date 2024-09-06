"""Tests gridworks.event.gt.sh.status type, version 000"""

from gjk.types import GridworksEventGtShStatus


def test_gridworks_event_gt_sh_status_generated() -> None:
    d = {
        "MessageId": "2952731d-a415-44de-b37c-f5f865dee77b",
        "TimeNS": 1699886100019488593,
        "Src": "hw1.isone.me.versant.keene.beech.scada",
        "Status": {
            "FromGNodeAlias": "hw1.isone.me.versant.keene.beech.scada",
            "FromGNodeId": "b98eadcf-aeff-4ef6-96f0-c8641bae6909",
            "AboutGNodeAlias": "dummy.ta",
            "SlotStartUnixS": 1699885800,
            "ReportingPeriodS": 300,
            "SimpleTelemetryList": [
                {
                    "ShNodeAlias": "a.dist.flow",
                    "TelemetryName": "GallonsTimes100",
                    "ValueList": [
                        478060,
                        478060,
                        478060,
                        478060,
                        478060,
                        478060,
                        478060,
                        478060,
                        478060,
                    ],
                    "ReadTimeUnixMsList": [
                        1699885826322,
                        1699885856324,
                        1699885886323,
                        1699885916871,
                        1699885948047,
                        1699885978862,
                        1699886008715,
                        1699886039477,
                        1699886069538,
                    ],
                    "TypeName": "gt.sh.simple.telemetry.status",
                    "Version": "100",
                }
            ],
            "MultipurposeTelemetryList": [
                {
                    "AboutNodeAlias": "a.hp.fossil.lwt.temp",
                    "SensorNodeAlias": "a.s.analog.temp",
                    "TelemetryName": "WaterTempCTimes1000",
                    "ValueList": [-42027, -37525, -36790, -37600, -37581],
                    "ReadTimeUnixMsList": [
                        1699885810070,
                        1699885870269,
                        1699885930078,
                        1699885990620,
                        1699886050455,
                    ],
                    "TypeName": "gt.sh.multipurpose.telemetry.status",
                    "Version": "100",
                },
            ],
            "BooleanactuatorCmdList": [],
            "StatusUid": "55faec9b-7ce6-4a64-9d5d-e07e20cf6e15",
            "TypeName": "gt.sh.status",
            "Version": "110",
        },
        "TypeName": "gridworks.event.gt.sh.status",
        "Version": "000",
    }

    t = GridworksEventGtShStatus.from_dict(d)
    assert t.to_dict() == d
