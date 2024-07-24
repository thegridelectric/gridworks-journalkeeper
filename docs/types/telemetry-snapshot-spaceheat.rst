TelemetrySnapshotSpaceheat
==========================
Python pydantic class corresponding to json type `telemetry.snapshot.spaceheat`, version `000`.

.. autoclass:: gjk.types.TelemetrySnapshotSpaceheat
    :members:

**ReportTimeUnixMs**:
    - Description: ReportTimeUnixMs.The time, in unix ms, that the SCADA creates this type. It may not be when the SCADA sends the type to the atn (for example if Internet is down).
    - Format: ReasonableUnixTimeMs

**AboutNodeAliasList**:
    - Description: AboutNodeAliases.The list of Spaceheat nodes in the snapshot. 
    - Format: LeftRightDot

**ValueList**:
    - Description: ValueList.

**TelemetryNameList**:
    - Description: 

**TypeName**:
    - Description: All GridWorks Versioned Types have a fixed TypeName, which is a string of lowercase alphanumeric words separated by periods, most significant word (on the left) starting with an alphabet character, and final word NOT all Hindu-Arabic numerals.

**Version**:
    - Description: All GridWorks Versioned Types have a fixed version, which is a string of three Hindu-Arabic numerals.



.. autoclass:: gjk.types.telemetry_snapshot_spaceheat.check_is_left_right_dot
    :members:


.. autoclass:: gjk.types.telemetry_snapshot_spaceheat.check_is_reasonable_unix_time_ms
    :members:


.. autoclass:: gjk.types.TelemetrySnapshotSpaceheat_Maker
    :members:

