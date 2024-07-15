

SDK for `gridworks-protocol <https://pypi.org/project/gridworks-protocol/>`_  Types
===========================================================================

The Python classes enumerated below provide an interpretation of gridworks-protocol
type instances (serialized JSON) as Python objects. Types are the building
blocks for all GridWorks APIs. You can read more about how they work
`here <https://gridworks.readthedocs.io/en/latest/api-sdk-abi.html>`_, and
examine their API specifications `here <apis/types.html>`_.
The Python classes below also come with methods for translating back and
forth between type instances and Python objects.


.. automodule:: gwp.types

.. toctree::
   :maxdepth: 1
   :caption: TYPE SDKS

    BatchedReadings  <types/batched-readings>
    ChannelReadings  <types/channel-readings>
    DataChannelGt  <types/data-channel-gt>
    FsmAtomicReport  <types/fsm-atomic-report>
    FsmFullReport  <types/fsm-full-report>
    GridworksEventGtShStatus  <types/gridworks-event-gt-sh-status>
    GridworksEventSnapshotSpaceheat  <types/gridworks-event-snapshot-spaceheat>
    GtShBooleanactuatorCmdStatus  <types/gt-sh-booleanactuator-cmd-status>
    GtShMultipurposeTelemetryStatus  <types/gt-sh-multipurpose-telemetry-status>
    GtShSimpleTelemetryStatus  <types/gt-sh-simple-telemetry-status>
    GtShStatus  <types/gt-sh-status>
    HeartbeatA  <types/heartbeat-a>
    SnapshotSpaceheat  <types/snapshot-spaceheat>
    TelemetrySnapshotSpaceheat  <types/telemetry-snapshot-spaceheat>
