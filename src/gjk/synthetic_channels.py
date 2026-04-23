import uuid

from gw_data.db.models import ReadingChannelSql
from sema.runtime.enums import Gw1Unit


class SyntheticChannel:
    CHANNEL_TYPE = "gjk.synthetic"

    def __init__(self, name: str, display_name: str, unit: Gw1Unit):
        self.name = name
        self.display_name = display_name
        self.unit = unit

    def to_db_channel(self, terminal_asset_alias):
        return ReadingChannelSql(
            id=uuid.uuid4(),
            name=self.name,
            terminal_asset_alias=terminal_asset_alias,
            display_name=self.display_name,
            unit=self.unit,
            unit_type=Gw1Unit.enum_name(),
            channel_type=self.CHANNEL_TYPE,
        )


ALL_SYNTHETIC_CHANNELS = [
    SyntheticChannel(
        name="hp-elec-in",
        display_name="Heat Pump Electrical Power In",
        unit=Gw1Unit.WattHours,
    ),
    SyntheticChannel(
        name="hp-heat-out",
        display_name="Heat Pump Thermal Power Out",
        unit=Gw1Unit.WattHours,
    ),
    SyntheticChannel(
        name="hp-delta-t", display_name="Heat Pump Delta-T", unit=Gw1Unit.FahrenheitX100
    ),
    SyntheticChannel(
        name="hp-cop", display_name="Heat Pump COP", unit=Gw1Unit.Unitless
    ),
    SyntheticChannel(
        name="dist-heat",
        display_name="Distribution Thermal Power",
        unit=Gw1Unit.WattHours,
    ),
    SyntheticChannel(
        name="dist-delta-t",
        display_name="Distribution Delta-T",
        unit=Gw1Unit.FahrenheitX100,
    ),
    SyntheticChannel(
        name="store-heat-change",
        display_name="Store Thermal Power Change",
        unit=Gw1Unit.WattHours,
    ),
    SyntheticChannel(
        name="store-delta-t", display_name="Store Delta-T", unit=Gw1Unit.FahrenheitX100
    ),
    SyntheticChannel(
        name="store-flow-rate", display_name="Store Flow Rate", unit=Gw1Unit.GpmX100
    ),
    SyntheticChannel(
        name="zone1-heatcall", display_name="Zone 1 Heat Call", unit=Gw1Unit.Unitless
    ),
    SyntheticChannel(
        name="zone2-heatcall", display_name="Zone 2 Heat Call", unit=Gw1Unit.Unitless
    ),
    SyntheticChannel(
        name="zone3-heatcall", display_name="Zone 3 Heat Call", unit=Gw1Unit.Unitless
    ),
    SyntheticChannel(
        name="zone4-heatcall", display_name="Zone 4 Heat Call", unit=Gw1Unit.Unitless
    ),
    # From weather.forecast
    SyntheticChannel(
        name="forecast-oat",
        display_name="Forecast Outside Air Temperature",
        unit=Gw1Unit.FahrenheitX100,
    ),
    SyntheticChannel(
        name="forecast-ws",
        display_name="Forecast Wind Speed",
        unit=Gw1Unit.MilesPerHour,
    ),
    # From flo.params.house0
    SyntheticChannel(
        name="total-usd-per-mwh", display_name="Total $/MWh", unit=Gw1Unit.Unitless
    ),
    SyntheticChannel(
        name="lmp-usd-per-mwh", display_name="LMP $/MWh", unit=Gw1Unit.Unitless
    ),
    SyntheticChannel(
        name="buffer-heat-available",
        display_name="Available Buffer Heat",
        unit=Gw1Unit.WattHours,
    ),
]


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
