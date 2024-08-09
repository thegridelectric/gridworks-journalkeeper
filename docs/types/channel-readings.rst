ChannelReadings
==========================
Python pydantic class corresponding to json type `channel.readings`, version `000`.

.. autoclass:: gjk.types.ChannelReadings
    :members:

**ChannelId**:
    - Description: Channel Od.The globally unique identifier of the Data Channel for this  batch of timestamped values.
    - Format: UuidCanonicalTextual

**ValueList**:
    - Description: List of Values.Refer to the associated DataChannel to understand the meaning of the these readings.

**ScadaReadTimeUnixMsList**:
    - Description: List of Read Times.The times that the MultipurposeSensor took the readings, in unix milliseconds
    - Format: ReasonableUnixTimeMs

**TypeName**:
    - Description: All GridWorks Versioned Types have a fixed TypeName, which is a string of lowercase alphanumeric words separated by periods, most significant word (on the left) starting with an alphabet character, and final word NOT all Hindu-Arabic numerals.

**Version**:
    - Description: All GridWorks Versioned Types have a fixed version, which is a string of three Hindu-Arabic numerals.



.. autoclass:: gjk.types.channel_readings.check_is_uuid_canonical_textual
    :members:


.. autoclass:: gjk.types.channel_readings.check_is_reasonable_unix_time_ms
    :members:


.. autoclass:: gjk.types.ChannelReadings_Maker
    :members:
