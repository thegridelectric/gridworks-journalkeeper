"""Tests spaceheat.node.gt type, version 200"""

from gjk.enums import ActorClass
from gjk.named_types import SpaceheatNodeGt


def test_spaceheat_node_gt_generated() -> None:
    d = {
        "Name": "aquastat-ctrl-relay",
        "ActorHierarchyName": "pi2.aquastat-ctrl-relay",
        "Handle": "admin.aquastat-ctrl-relay",
        "ActorClass": "Relay",
        "DisplayName": "Aquastat Control Relay",
        "ComponentIdId": "80f95280-e999-49e0-a0e4-a7faf3b5b3bd",
        "ShNodeId": "92091523-4fa7-4a3e-820b-fddee089222f",
        "TypeName": "spaceheat.node.gt",
        "Version": "200",
    }

    assert SpaceheatNodeGt.from_dict(d).to_dict() == d

    ######################################
    # Behavior on unknown enum values: sends to default
    ######################################

    d2 = dict(d, ActorClass="unknown_enum_thing")
    assert SpaceheatNodeGt.from_dict(d2).actor_class == ActorClass.default()
