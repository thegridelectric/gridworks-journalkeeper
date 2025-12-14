"""
Tests for enum problem.type.000 from the GridWorks Type Registry.
"""

from gjk.enums import ProblemType


def test_problem_type() -> None:
    assert set(ProblemType.values()) == {
        "error",
        "warning",
    }

    assert ProblemType.default() == ProblemType.error
    assert ProblemType.enum_name() == "problem.type"
    assert ProblemType.enum_version() == "000"

    assert ProblemType.version("error") == "000"
    assert ProblemType.version("warning") == "000"

    for value in ProblemType.values():
        symbol = ProblemType.value_to_symbol(value)
        assert ProblemType.symbol_to_value(symbol) == value
