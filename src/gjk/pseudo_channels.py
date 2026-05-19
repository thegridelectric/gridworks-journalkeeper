# A PseudoChannel is something that:
#   1. We store in the database as a channel
#   2. We store readings for (in the readings table)
#   3. Is not a DataChannel or a DerivedChannel defined in the hardware layout
#
# This includes things like price, weather, ShNode states, etc.


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

    # TODO include pseudo-channels from these other message persistor types
    # yield from WeatherForecastPersistor.get_pseudo_channels()
    # yield from FloParamsPersistor.get_pseudo_channels()


# ALL_PSEUDO_CHANNELS = [].extend()

#     # From weather.forecast
#     PseudoChannel(
#         name="forecast-oat",
#         display_name="Forecast Outside Air Temperature",
#         unit=Gw1Unit.FahrenheitX100,
#     ),
#     PseudoChannel(
#         name="forecast-ws",
#         display_name="Forecast Wind Speed",
#         unit=Gw1Unit.MilesPerHour,
#     ),
#     # From flo.params.house0
#     PseudoChannel(
#         name="total-usd-per-mwh", display_name="Total $/MWh", unit=Gw1Unit.Unitless
#     ),
#     PseudoChannel(
#         name="lmp-usd-per-mwh", display_name="LMP $/MWh", unit=Gw1Unit.Unitless
#     ),
#     PseudoChannel(
#         name="buffer-heat-available",
#         display_name="Available Buffer Heat",
#         unit=Gw1Unit.WattHours,
#     ),
# ]


# Still left to handle?

# From flo.params.house0
# Derived --> True if FLO is active. Do we really need this?
# flo=flo_tf,
# Obsolete --> These used to be parsed out of the FLO messages but are now commented out
# alpha=alpha,
# beta=beta,
# gamma=gamma,
# intermediate_power_kw=intermediate_power_kw,
# intermediate_rswt=intermediate_rswt,
# dd_power_kw=dd_power_kw,
# dd_rswt=dd_rswt,
# dd_delta_t=dd_delta_t,

# From atn.bid -- not a number; rather, a string of number pairs representing the bid. Makes no sense for a reading.
# bid=bid,

# No longer needed
# buffer_used_kwh_before_charge=buffer_used_kwh_before_charge
