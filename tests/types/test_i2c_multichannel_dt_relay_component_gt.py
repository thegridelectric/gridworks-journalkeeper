"""Tests i2c.multichannel.dt.relay.component.gt type, version 002"""

from gjk.named_types import I2cMultichannelDtRelayComponentGt


def test_i2c_multichannel_dt_relay_component_gt_generated() -> None:
    d = {
        "ComponentId": "798fe14a-4073-41eb-bce2-075906aee6bb",
        "ComponentAttributeClassId": "69f101fc-22e4-4caa-8103-50b8aeb66028",
        "I2cAddressList": [],
        "ConfigList": [],
        "DisplayName": "relay for first elt in tank",
        "HwUid": "abc123",
        "TypeName": "i2c.multichannel.dt.relay.component.gt",
        "Version": "002",
    }

    assert I2cMultichannelDtRelayComponentGt.from_dict(d).to_dict() == d
