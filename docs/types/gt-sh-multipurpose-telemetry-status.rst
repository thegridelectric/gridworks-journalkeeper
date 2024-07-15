GtShMultipurposeTelemetryStatus
==========================
Python pydantic class corresponding to json type `gt.sh.multipurpose.telemetry.status`, version `100`.

.. autoclass:: gwp.types.GtShMultipurposeTelemetryStatus
    :members:

**AboutNodeAlias**:
    - Description: AboutNodeAlias.The SpaceheatNode representing the physical object that the sensor reading is collecting data about. For example, a multipurpose temp sensor that reads 12 temperatures would have data for 12 different AboutNodeAliases, including say `a.tank1.temp1` for a temp sensor at the top of a water tank.
    - Format: LeftRightDot

**SensorNodeAlias**:
    - Description: SensorNodeAlias.The alias of the SpaceheatNode representing the telemetry device

**TelemetryName**:
    - Description: TelemetryName.The TelemetryName of the readings. This is used to interpet the meaning of the reading values. For example, WaterTempCTimes1000 means the reading is measuring the a reading of 37 deg C.

**ValueList**:
    - Description: List of Values.The values of the readings. 

**ReadTimeUnixMsList**:
    - Description: List of Read Times.The times that the MultipurposeSensor took the readings, in unix milliseconds
    - Format: ReasonableUnixTimeMs

**TypeName**:
    - Description: All GridWorks Versioned Types have a fixed TypeName, which is a string of lowercase alphanumeric words separated by periods, most significant word (on the left) starting with an alphabet character, and final word NOT all Hindu-Arabic numerals.

**Version**:
    - Description: All GridWorks Versioned Types have a fixed version, which is a string of three Hindu-Arabic numerals.



.. autoclass:: gwp.types.gt_sh_multipurpose_telemetry_status.check_is_left_right_dot
    :members:


.. autoclass:: gwp.types.gt_sh_multipurpose_telemetry_status.check_is_reasonable_unix_time_ms
    :members:


.. autoclass:: gwp.types.GtShMultipurposeTelemetryStatus_Maker
    :members:

