# A PseudoChannel is something that:
#   1. We store in the database as a channel
#   2. We store readings for (in the readings table)
#   3. Is not a DataChannel or a DerivedChannel defined in the hardware layout
#
# This includes things like price, weather, ShNode states, etc.
#
# Some persistors manage their own pseudo-channels as part of persisting their readings.
# But others can use this class to manage it for them, as part of the LayoutLite peristence.


class PseudoChannel:
    CHANNEL_TYPE = "gjk.pseudo"

    def __init__(self, name: str, display_name: str, unit, unit_type: str):
        self.name = name
        self.display_name = display_name
        self.unit = unit
        self.unit_type = unit_type


_REGISTERED_CHANNELS = []


def register_pseudo_channels(channels: list[PseudoChannel]):
    _REGISTERED_CHANNELS.extend(channels)


def get_pseudo_channels():
    yield from _REGISTERED_CHANNELS
