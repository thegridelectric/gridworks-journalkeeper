"""
GridWorks Enums used in gwp, the Application Shared Language (ASL) used by SCADA
devices and AtomicTNodes to communicate with each other. These enums play a specific structural
role as semantic "glue" within ASLs.

Key attributes:
  - Enum values are translated into "GridWorks Type Enum Symbols" (GtEnumSymbols) when embedded
  in a serialized type sent as a message from one Application and/or Actor to another.
  - Each Enum has a unique name in the type registry (like spaceheat.telemetry.name), along
  with a version (like 001).
  - That name are interpretted locally in the SDK and do not necessarily carry the larger
  context of the unique type registry name (for example gwp uses TelemetryName, since
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

from gwp.enums.fsm_action_type import FsmActionType
from gwp.enums.fsm_event_type import FsmEventType
from gwp.enums.fsm_name import FsmName
from gwp.enums.fsm_report_type import FsmReportType
from gwp.enums.telemetry_name import TelemetryName


__all__ = [
    "FsmActionType",  # [sh.fsm.action.type.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#shfsmactiontype)
    "FsmEventType",  # [sh.fsm.event.type.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#shfsmeventtype)
    "FsmName",  # [sh.fsm.name.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#shfsmname)
    "FsmReportType",  # [fsm.report.type.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#fsmreporttype)
    "TelemetryName",  # [spaceheat.telemetry.name.001](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#spaceheattelemetryname)
]
