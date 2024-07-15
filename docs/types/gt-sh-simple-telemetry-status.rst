GtShSimpleTelemetryStatus
==========================
Python pydantic class corresponding to json type `gt.sh.simple.telemetry.status`, version `100`.

.. autoclass:: gwp.types.GtShSimpleTelemetryStatus
    :members:

**ShNodeAlias**:
    - Description: SpaceheatNodeAlias.The Alias of the SimpleSensor associated to the readings
    - Format: LeftRightDot

**TelemetryName**:
    - Description: TelemetryName.The TelemetryName of the readings. This is used to interpet the meaning of the
        reading values. For example, WaterTempCTimes1000 means the reading is measuring
        the temperature of water, in Celsius multiplied by 1000. So a value of 37000 would be
        a reading of 37 deg C.

**ValueList**:
    - Description: List of Values.The values of the readings. 

**ReadTimeUnixMsList**:
    - Description: List of Read Times.The times that the SImpleSensor took the readings, in unix milliseconds
    - Format: ReasonableUnixTimeMs

**TypeName**:
    - Description: All GridWorks Versioned Types have a fixed TypeName, which is a string of lowercase alphanumeric words separated by periods, most significant word (on the left) starting with an alphabet character, and final word NOT all Hindu-Arabic numerals.

**Version**:
    - Description: All GridWorks Versioned Types have a fixed version, which is a string of three Hindu-Arabic numerals.



.. autoclass:: gwp.types.gt_sh_simple_telemetry_status.check_is_left_right_dot
    :members:


.. autoclass:: gwp.types.gt_sh_simple_telemetry_status.check_is_reasonable_unix_time_ms
    :members:


.. autoclass:: gwp.types.GtShSimpleTelemetryStatus_Maker
    :members:

