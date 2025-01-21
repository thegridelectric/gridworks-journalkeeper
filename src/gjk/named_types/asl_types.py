"""List of all the types used by the actor."""

from typing import Dict, List, no_type_check

from gw.named_types import GwBase

from gjk.named_types.atn_bid import AtnBid
from gjk.named_types.channel_config import ChannelConfig
from gjk.named_types.channel_readings import ChannelReadings
from gjk.named_types.data_channel_gt import DataChannelGt
from gjk.named_types.energy_instruction import EnergyInstruction
from gjk.named_types.flo_params_house0 import FloParamsHouse0
from gjk.named_types.fsm_atomic_report import FsmAtomicReport
from gjk.named_types.fsm_event import FsmEvent
from gjk.named_types.fsm_full_report import FsmFullReport
from gjk.named_types.gridworks_event_problem import GridworksEventProblem
from gjk.named_types.ha1_params import Ha1Params
from gjk.named_types.heartbeat_a import HeartbeatA
from gjk.named_types.heating_forecast import HeatingForecast
from gjk.named_types.i2c_multichannel_dt_relay_component_gt import (
    I2cMultichannelDtRelayComponentGt,
)
from gjk.named_types.keyparam_change_log import KeyparamChangeLog
from gjk.named_types.latest_price import LatestPrice
from gjk.named_types.layout_lite import LayoutLite
from gjk.named_types.machine_states import MachineStates
from gjk.named_types.pico_flow_module_component_gt import PicoFlowModuleComponentGt
from gjk.named_types.pico_tank_module_component_gt import PicoTankModuleComponentGt
from gjk.named_types.power_watts import PowerWatts
from gjk.named_types.price_quantity_unitless import PriceQuantityUnitless
from gjk.named_types.relay_actor_config import RelayActorConfig
from gjk.named_types.report import Report
from gjk.named_types.report_event import ReportEvent
from gjk.named_types.scada_params import ScadaParams
from gjk.named_types.snapshot_spaceheat import SnapshotSpaceheat
from gjk.named_types.spaceheat_node_gt import SpaceheatNodeGt
from gjk.named_types.synth_channel_gt import SynthChannelGt
from gjk.named_types.ticklist_hall import TicklistHall
from gjk.named_types.ticklist_hall_report import TicklistHallReport
from gjk.named_types.ticklist_reed import TicklistReed
from gjk.named_types.ticklist_reed_report import TicklistReedReport
from gjk.named_types.weather import Weather
from gjk.named_types.weather_forecast import WeatherForecast
from gjk.old_types import GridworksEventSnapshotSpaceheat
from gjk.old_types.batched_readings import BatchedReadings
from gjk.old_types.channel_readings_000 import ChannelReadings000
from gjk.old_types.channel_readings_001 import ChannelReadings001
from gjk.old_types.flo_params_house0_000 import FloParamsHouse0_000
from gjk.old_types.gridworks_event_gt_sh_status import GridworksEventGtShStatus
from gjk.old_types.gridworks_event_report import GridworksEventReport
from gjk.old_types.gt_sh_booleanactuator_cmd_status import GtShBooleanactuatorCmdStatus
from gjk.old_types.gt_sh_multipurpose_telemetry_status import (
    GtShMultipurposeTelemetryStatus,
)
from gjk.old_types.gt_sh_simple_telemetry_status import GtShSimpleTelemetryStatus
from gjk.old_types.gt_sh_status import GtShStatus
from gjk.old_types.ha1_params_000 import Ha1Params000
from gjk.old_types.ha1_params_001 import Ha1Params001
from gjk.old_types.i2c_multichannel_dt_relay_component_gt_001 import (
    I2cMultichannelDtRelayComponentGt001,
)
from gjk.old_types.layout_event import LayoutEvent
from gjk.old_types.layout_lite_000 import LayoutLite000
from gjk.old_types.layout_lite_001 import LayoutLite001
from gjk.old_types.layout_lite_002 import LayoutLite002
from gjk.old_types.layout_lite_003 import LayoutLite003
from gjk.old_types.my_channels import MyChannels
from gjk.old_types.my_channels_event import MyChannelsEvent
from gjk.old_types.report_000 import Report000
from gjk.old_types.scada_params_001 import ScadaParams001
from gjk.old_types.scada_params_002 import ScadaParams002
from gjk.old_types.snapshot_spaceheat_000 import SnapshotSpaceheat000
from gjk.old_types.snapshot_spaceheat_001 import SnapshotSpaceheat001
from gjk.old_types.telemetry_snapshot_spaceheat import TelemetrySnapshotSpaceheat

TypeByName: Dict[str, GwBase] = {}


@no_type_check
def types() -> List[GwBase]:
    return [
        BatchedReadings,
        ChannelReadings000,
        ChannelReadings001,
        FloParamsHouse0_000,
        GridworksEventGtShStatus,
        GridworksEventReport,
        GridworksEventSnapshotSpaceheat,
        GtShBooleanactuatorCmdStatus,
        GtShMultipurposeTelemetryStatus,
        GtShSimpleTelemetryStatus,
        GtShStatus,
        Ha1Params000,
        Ha1Params001,
        I2cMultichannelDtRelayComponentGt001,
        LayoutEvent,
        LayoutLite000,
        LayoutLite001,
        LayoutLite002,
        LayoutLite003,
        MyChannels,
        MyChannelsEvent,
        Report000,
        ScadaParams001,
        ScadaParams002,
        SnapshotSpaceheat000,
        SnapshotSpaceheat001,
        TelemetrySnapshotSpaceheat,
        AtnBid,
        ChannelConfig,
        ChannelReadings,
        DataChannelGt,
        EnergyInstruction,
        FloParamsHouse0,
        FsmAtomicReport,
        FsmEvent,
        FsmFullReport,
        GridworksEventProblem,
        Ha1Params,
        HeartbeatA,
        HeatingForecast,
        I2cMultichannelDtRelayComponentGt,
        KeyparamChangeLog,
        LatestPrice,
        LayoutLite,
        MachineStates,
        PicoFlowModuleComponentGt,
        PicoTankModuleComponentGt,
        PowerWatts,
        PriceQuantityUnitless,
        RelayActorConfig,
        Report,
        ReportEvent,
        ScadaParams,
        SnapshotSpaceheat,
        SpaceheatNodeGt,
        SynthChannelGt,
        TicklistHall,
        TicklistHallReport,
        TicklistReed,
        TicklistReedReport,
        Weather,
        WeatherForecast,
    ]


for t in types():
    try:
        TypeByName[t.type_name_value()] = t
    except:
        print(f"Problem w {t}")
