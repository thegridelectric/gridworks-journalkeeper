"""
Tests for enum pico.cycler.state.000 from the GridWorks Type Registry.
"""

from gjk.enums import PicoCyclerState


def test_pico_cycler_state() -> None:
    assert set(PicoCyclerState.values()) == {
        "Dormant",
        "PicosLive",
        "RelayOpening",
        "RelayOpen",
        "RelayClosing",
        "PicosRebooting",
        "AllZombies",
    }

    assert PicoCyclerState.default() == PicoCyclerState.PicosLive
    assert PicoCyclerState.enum_name() == "pico.cycler.state"
    assert PicoCyclerState.enum_version() == "000"

    assert PicoCyclerState.version("Dormant") == "000"
    assert PicoCyclerState.version("PicosLive") == "000"
    assert PicoCyclerState.version("RelayOpening") == "000"
    assert PicoCyclerState.version("RelayOpen") == "000"
    assert PicoCyclerState.version("RelayClosing") == "000"
    assert PicoCyclerState.version("PicosRebooting") == "000"
    assert PicoCyclerState.version("AllZombies") == "000"

    for value in PicoCyclerState.values():
        symbol = PicoCyclerState.value_to_symbol(value)
        assert PicoCyclerState.symbol_to_value(symbol) == value
