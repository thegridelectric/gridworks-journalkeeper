SpaceheatNodeGt
==========================
Python pydantic class corresponding to json type `spaceheat.node.gt`, version `200`.

.. autoclass:: gwp.types.SpaceheatNodeGt
    :members:

**Name**:
    - Description: Name.Human readable immutable identifier. alpha-numeric words, first wording starting with an alphabet character, separated by hyphens. No dots.
    - Format: SpaceheatName

**ActorHierarchyName**:
    - Description: ActorHierarchy.This shows the parent-child chain of responsibility for ShNodes that are actors. For example, if h.aquastat-ctrl-relay is the ActorHierarchy, then the actor whose ActorHierarchyName is `h` is responsible for spawning, monitoring, killing and restarting this actor.
    - Format: HandleName

**Handle**:
    - Description: Handle.Word structure shows Terminal Asset Finite State Machine hierarchy. Locally unique, but mutable.  If there is a dot, then the predecessor handle (handle with the final word removed) is the handle for the 'boss' node.  Only nodes with actors that can take actions that change the state of the Terminal Asset have dots in their handles. For example, the analog temperature sensor in the LocalName description above does NOT take actions and its handle would likely be analog-temp. If a node's actor CAN take actions that change the state of the TerminalAsset, it only takes commands from its boss node. For example, a relay actor will only agree to energize or de-energize its relay as a result of a command from its (current) boss. 
    - Format: HandleName

**ActorClass**:
    - Description: Actor Class.Used to select the actor's code.

**DisplayName**:
    - Description: Display Name.For user interfaces that don't want to show the local name or handle.

**ComponentId**:
    - Description: Unique identifier for Spaceheat Node's Component.Used if a Spaceheat Node is associated with a physical device.

**InPowerMetering**:
    - Description: In Power Metering.This exists and is True if the SpaceheatNode is part of the power metering that is used for market participation. Small loads like circulator pumps and fans may be metered to determine their behavior but are are likely NOT part of the power metering used for market participation. 

**ShNodeId**:
    - Description: Id.Immutable identifier for one of the Spaceheat Nodes of a Terminal Asset.   Globally unique - i.e. across all Space Heat Nodes for all Terminal Assets.
    - Format: UuidCanonicalTextual

**TypeName**:
    - Description: All GridWorks Versioned Types have a fixed TypeName, which is a string of lowercase alphanumeric words separated by periods, most significant word (on the left) starting with an alphabet character, and final word NOT all Hindu-Arabic numerals.

**Version**:
    - Description: All GridWorks Versioned Types have a fixed version, which is a string of three Hindu-Arabic numerals.



.. autoclass:: gwp.types.spaceheat_node_gt.check_is_uuid_canonical_textual
    :members:


.. autoclass:: gwp.types.spaceheat_node_gt.check_is_spaceheat_name
    :members:


.. autoclass:: gwp.types.SpaceheatNodeGt_Maker
    :members:

