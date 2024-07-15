FsmAtomicReport
==========================
Python pydantic class corresponding to json type `fsm.atomic.report`, version `000`.

.. autoclass:: gwp.types.FsmAtomicReport
    :members:

**FromHandle**:
    - Description: From Handle.The Name (as opposed to the handle) of the Spaceheat Node actor issuing the Finite State Machine report.  The actor is meant to realize and be the authority on the FSM in question. Its handle reflects the state it is in.
    - Format: SpaceheatName

**AboutFsm**:
    - Description: About Fsm.The finite state machine this message is about.

**ReportType**:
    - Description: Report Type.Is this reporting an event, an action, or some other thing related to a finite state machine?

**ActionType**:
    - Description: Action Type.The FiniteState Machine Action taken

**Action**:
    - Description: Action.Will typically be a number, usually an integer. For example, if ActionType is RelayPinSet, then RelayPinSet.DeEnergized = 0 and RelayPinSet.Energized = 1.

**EventType**:
    - Description: Event Type.

**Event**:
    - Description: Event.

**FromState**:
    - Description: From State.The state of the FSM prior to triggering event.

**ToState**:
    - Description: To State.The state of the FSM after the triggering event.

**UnixTimeMs**:
    - Description: Unix Time in Milliseconds.
    - Format: ReasonableUnixTimeMs

**TriggerId**:
    - Description: TriggerId.Reference uuid for the triggering event that started a cascade of transitions, events and  side-effect actions - of which this report is one.
    - Format: UuidCanonicalTextual

**TypeName**:
    - Description: All GridWorks Versioned Types have a fixed TypeName, which is a string of lowercase alphanumeric words separated by periods, most significant word (on the left) starting with an alphabet character, and final word NOT all Hindu-Arabic numerals.

**Version**:
    - Description: All GridWorks Versioned Types have a fixed version, which is a string of three Hindu-Arabic numerals.



.. autoclass:: gwp.types.fsm_atomic_report.check_is_uuid_canonical_textual
    :members:


.. autoclass:: gwp.types.fsm_atomic_report.check_is_spaceheat_name
    :members:


.. autoclass:: gwp.types.fsm_atomic_report.check_is_reasonable_unix_time_ms
    :members:


.. autoclass:: gwp.types.FsmAtomicReport_Maker
    :members:

