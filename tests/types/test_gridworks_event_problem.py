"""Tests gridworks.event.problem type, version 001"""

from gjk.enums import ProblemType
from gjk.named_types import GridworksEventProblem


def test_gridworks_event_problem_generated() -> None:
    d = {
        "Src": "hw1.isone.me.versant.keene.oak.scada",
        "ProblemType": "error",
        "Summary": "primary-flow",
        "Details": "Problems: 0 errors, 1 warnings, max: 10\nWarnings:\n 0: Pico down\n",
        "TimeCreatedMs": 1730813943068,
        "MessageId": "50825d71-ac42-487d-b200-7f5effaccbd3",
        "TypeName": "gridworks.event.problem",
        "Version": "001",
    }

    assert GridworksEventProblem.from_dict(d).to_dict() == d

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, ProblemType="unknown_enum_thing")
    assert GridworksEventProblem.from_dict(d2).problem_type == ProblemType.default()
