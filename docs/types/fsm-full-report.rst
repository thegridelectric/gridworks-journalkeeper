FsmFullReport
==========================
Python pydantic class corresponding to json type `fsm.full.report`, version `000`.

.. autoclass:: gjk.types.FsmFullReport
    :members:

**FromName**:
    - Description: From Name.The name (not the handle, so immutable) of the Node issuing the report. This will typically be the scada node itself.
    - Format: SpaceheatName

**TriggerId**:
    - Description: TriggerId.Reference uuid for the triggering event that started the cascade of side-effect actions, events and transitions captured in this report 
    - Format: UuidCanonicalTextual

**AtomicList**:
    - Description: Atomic List.The list of cascading events, transitions and actions triggered by a single high-level event in a hierarchical finite state machine.

**TypeName**:
    - Description: All GridWorks Versioned Types have a fixed TypeName, which is a string of lowercase alphanumeric words separated by periods, most significant word (on the left) starting with an alphabet character, and final word NOT all Hindu-Arabic numerals.

**Version**:
    - Description: All GridWorks Versioned Types have a fixed version, which is a string of three Hindu-Arabic numerals.



.. autoclass:: gjk.types.fsm_full_report.check_is_uuid_canonical_textual
    :members:


.. autoclass:: gjk.types.fsm_full_report.check_is_spaceheat_name
    :members:


.. autoclass:: gjk.types.FsmFullReport_Maker
    :members:

