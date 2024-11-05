"""
GridWorks Enums used in gjk, the Application Shared Language (ASL) used by SCADA
devices and AtomicTNodes to communicate with each other. These enums play a specific structural
role as semantic "glue" within ASLs.

Key attributes:
  - Enum values are translated into "GridWorks Type Enum Symbols" (GtEnumSymbols) when embedded
  in a serialized type sent as a message from one Application and/or Actor to another.
  - Each Enum has a unique name in the type registry (like spaceheat.telemetry.name), along
  with a version (like 001).
  - That name are interpretted locally in the SDK and do not necessarily carry the larger
  context of the unique type registry name (for example gjk uses TelemetryName, since
  the `spaceheat` context goes without saying).
  - Each Value/Symbol pair also has a version. Value/Symbol pairs cannot be changed or removed.
  The only adjustments that can be made to an enum are adding more Value/Symbols. This is to
  support forwards- and backwards- compatability in GridWorks Types that use these enums.

If Enums are "glue", then GridWorks Types are the building blocks of SALs. Every SAL is comprised
of a set of shared GridWorks Types.

Application Shared Languages are an evolution of the concept of Application Programming Interfaces.
In a nutshell, an API can be viewed as a rather restricted version of an SAL, where only one application
has anything complex/interesting to say and, in general, the developers/owners of that application
have sole responsibility for managing the versioning and changing of that API. Note also that SALs
do not make any a priori assumption about the relationship (i.e. the default client/server for an API)
or the message delivery mechanism (i.e. via default GET/POST to RESTful URLs). For more information
on these ideas:
  - [GridWorks Enums](https://gridwork-type-registry.readthedocs.io/en/latest/types.html)
  - [GridWorks Types](https://gridwork-type-registry.readthedocs.io/en/latest/types.html)
  - [ASLs](https://gridwork-type-registry.readthedocs.io/en/latest/asls.html)
"""

from gjk.enums.change_aquastat_control import ChangeAquastatControl
from gjk.enums.change_heat_pump_control import ChangeHeatPumpControl
from gjk.enums.change_heatcall_source import ChangeHeatcallSource
from gjk.enums.change_lg_operating_mode import ChangeLgOperatingMode
from gjk.enums.change_primary_pump_control import ChangePrimaryPumpControl
from gjk.enums.change_primary_pump_state import ChangePrimaryPumpState
from gjk.enums.change_relay_pin import ChangeRelayPin
from gjk.enums.change_relay_state import ChangeRelayState
from gjk.enums.change_store_flow_direction import ChangeStoreFlowDirection
from gjk.enums.change_valve_state import ChangeValveState
from gjk.enums.fsm_action_type import FsmActionType
from gjk.enums.fsm_event_type import FsmEventType
from gjk.enums.fsm_name import FsmName
from gjk.enums.fsm_report_type import FsmReportType
from gjk.enums.g_node_role import GNodeRole
from gjk.enums.g_node_status import GNodeStatus
from gjk.enums.gpm_from_hz_method import GpmFromHzMethod
from gjk.enums.hz_calc_method import HzCalcMethod
from gjk.enums.kind_of_param import KindOfParam
from gjk.enums.make_model import MakeModel
from gjk.enums.problem_type import ProblemType
from gjk.enums.relay_closed_or_open import RelayClosedOrOpen
from gjk.enums.relay_pin_set import RelayPinSet
from gjk.enums.store_flow_direction import StoreFlowDirection
from gjk.enums.telemetry_name import TelemetryName
from gjk.enums.temp_calc_method import TempCalcMethod
from gjk.enums.unit import Unit

__all__ = [
    "ChangeAquastatControl",  # [change.aquastat.control.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#changeaquastatcontrol)
    "ChangeHeatPumpControl",  # [change.heat.pump.control.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#changeheatpumpcontrol)
    "ChangeHeatcallSource",  # [change.heatcall.source.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#changeheatcallsource)
    "ChangeLgOperatingMode",  # [change.lg.operating.mode.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#changelgoperatingmode)
    "ChangePrimaryPumpControl",  # [change.primary.pump.control.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#changeprimarypumpcontrol)
    "ChangePrimaryPumpState",  # [change.primary.pump.state.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#changeprimarypumpstate)
    "ChangeRelayPin",  # [change.relay.pin.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#changerelaypin)
    "ChangeRelayState",  # [change.relay.state.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#changerelaystate)
    "ChangeStoreFlowDirection",  # [change.store.flow.direction.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#changestoreflowdirection)
    "ChangeValveState",  # [change.valve.state.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#changevalvestate)
    "FsmActionType",  # [sh.fsm.action.type.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#shfsmactiontype)
    "FsmEventType",  # [sh.fsm.event.type.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#shfsmeventtype)
    "FsmName",  # [sh.fsm.name.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#shfsmname)
    "FsmReportType",  # [fsm.report.type.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#fsmreporttype)
    "GNodeRole",  # [g.node.role.001](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#gnoderole)
    "GNodeStatus",  # [g.node.status.100](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#gnodestatus)
    "GpmFromHzMethod",  # [gpm.from.hz.method.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#gpmfromhzmethod)
    "HzCalcMethod",  # [hz.calc.method.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#hzcalcmethod)
    "HzCalcMethod",  # [hz.calc.method.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#hzcalcmethod)
    "KindOfParam",  # [spaceheat.kind.of.param.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#spaceheatkindofparam)
    "MakeModel",  # [spaceheat.make.model.003](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#spaceheatmakemodel)
    "ProblemType",  # [problem.type.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#problemtype)
    "RelayClosedOrOpen",  # [relay.closed.or.open.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#relayclosedoropen)
    "RelayPinSet",  # [relay.pin.set.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#relaypinset)
    "StoreFlowDirection",  # [store.flow.direction.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#storeflowdirection)
    "TelemetryName",  # [spaceheat.telemetry.name.001](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#spaceheattelemetryname)
    "TempCalcMethod",  # [temp.calc.method.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#tempcalcmethod)
    "Unit",  # [spaceheat.unit.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#spaceheatunit)
]
