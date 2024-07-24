GtShBooleanactuatorCmdStatus
==========================
Python pydantic class corresponding to json type `gt.sh.booleanactuator.cmd.status`, version `101`.

.. autoclass:: gjk.types.GtShBooleanactuatorCmdStatus
    :members:

**ShNodeName**:
    - Description: SpaceheatNodeAlias.The alias of the spaceheat node that is getting actuated. For example, `a.elt1.relay` would likely indicate the relay for a resistive element.
    - Format: LeftRightDot

**RelayStateCommandList**:
    - Description: List of RelayStateCommands.This is only intended for use for relays where the two states are either closing a circuit so that power is on ( '1') or opening it ('0').

**CommandTimeUnixMsList**:
    - Description: List of Command Times.
    - Format: ReasonableUnixTimeMs

**TypeName**:
    - Description: All GridWorks Versioned Types have a fixed TypeName, which is a string of lowercase alphanumeric words separated by periods, most significant word (on the left) starting with an alphabet character, and final word NOT all Hindu-Arabic numerals.

**Version**:
    - Description: All GridWorks Versioned Types have a fixed version, which is a string of three Hindu-Arabic numerals.



.. autoclass:: gjk.types.gt_sh_booleanactuator_cmd_status.check_is_spaceheat_name
    :members:


.. autoclass:: gjk.types.gt_sh_booleanactuator_cmd_status.check_is_reasonable_unix_time_ms
    :members:


.. autoclass:: gjk.types.GtShBooleanactuatorCmdStatus_Maker
    :members:

