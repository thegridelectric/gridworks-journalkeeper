GridworksEventGtShStatus
==========================
Python pydantic class corresponding to json type `gridworks.event.gt.sh.status`, version `000`.

.. autoclass:: gwp.types.GridworksEventGtShStatus
    :members:

**MessageId**:
    - Description: MessageId.This is a unique immutable id assigned to the status payload when created by the SCADA. If the original message is not acked by the AtomicTNode, the entire gridworks.event is stored locally and re-sent later when AtomicTNode comms are re-established. (with this same MessageId) 
    - Format: UuidCanonicalTextual

**TimeNS**:
    - Description: The time in epoch nanoseconds that the SCADA created the status.

**Src**:
    - Description: The GNodeAlias of the SCADA sending the status.
    - Format: LeftRightDot

**Status**:
    - Description: 

**TypeName**:
    - Description: All GridWorks Versioned Types have a fixed TypeName, which is a string of lowercase alphanumeric words separated by periods, most significant word (on the left) starting with an alphabet character, and final word NOT all Hindu-Arabic numerals.

**Version**:
    - Description: All GridWorks Versioned Types have a fixed version, which is a string of three Hindu-Arabic numerals.



.. autoclass:: gwp.types.gridworks_event_gt_sh_status.check_is_uuid_canonical_textual
    :members:


.. autoclass:: gwp.types.gridworks_event_gt_sh_status.check_is_left_right_dot
    :members:


.. autoclass:: gwp.types.GridworksEventGtShStatus_Maker
    :members:

