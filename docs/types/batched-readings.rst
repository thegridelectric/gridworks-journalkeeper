BatchedReadings
==========================
Python pydantic class corresponding to json type `batched.readings`, version `000`.

.. autoclass:: gwp.types.BatchedReadings
    :members:

**FromGNodeAlias**:
    - Description: 
    - Format: LeftRightDot

**FromGNodeInstanceId**:
    - Description: 
    - Format: UuidCanonicalTextual

**AboutGNodeAlias**:
    - Description: 
    - Format: LeftRightDot

**SlotStartUnixS**:
    - Description: 
    - Format: ReasonableUnixTimeS

**BatchedTransmissionPeriodS**:
    - Description: 
    - Format: PositiveInteger

**MessageCreatedMs**:
    - Description: MessageCreatedMs.The SCADA timestamp for when this message was created. If the message is not acked by the AtomicTNode, the message is stored and sent again later - so the MessageCreatedMs may occur significantly before the timestamp for when the message is put into the persistent store.
    - Format: ReasonableUnixTimeMs

**DataChannelList**:
    - Description: DataChannel List.The list of data channels for which there is data getting reported in this batched reading. It is a subset of all the data channels for the SCADA - may not be all of them.

**ChannelReadingList**:
    - Description: 

**FsmActionList**:
    - Description: Finite State Machine Action List.FSM Actions (that is, side-effects of state machine transitions with real-world changes to the underlying TerminalAsset).

**FsmReportList**:
    - Description: Finite State Machine Report List.FSM Reports are the cacading events, actions and transitions caused by a single high-level event. There is duplication with the action list. 

**Id**:
    - Description: Batched Reading Id.Globally Unique identifier for a BatchedReadings message
    - Format: UuidCanonicalTextual

**TypeName**:
    - Description: All GridWorks Versioned Types have a fixed TypeName, which is a string of lowercase alphanumeric words separated by periods, most significant word (on the left) starting with an alphabet character, and final word NOT all Hindu-Arabic numerals.

**Version**:
    - Description: All GridWorks Versioned Types have a fixed version, which is a string of three Hindu-Arabic numerals.



.. autoclass:: gwp.types.batched_readings.check_is_reasonable_unix_time_s
    :members:


.. autoclass:: gwp.types.batched_readings.check_is_uuid_canonical_textual
    :members:


.. autoclass:: gwp.types.batched_readings.check_is_positive_integer
    :members:


.. autoclass:: gwp.types.batched_readings.check_is_left_right_dot
    :members:


.. autoclass:: gwp.types.BatchedReadings_Maker
    :members:

