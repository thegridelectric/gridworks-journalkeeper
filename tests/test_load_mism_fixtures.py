"""Wire shapes the OPS-498 prod load found that the walk-back's one-sample
scan missed; both are now accepted by the vendored snapshot.

- 2024-12-03: layout.lite:001 whose Ha1Params is labelled 000 but carries
  MaxEwtF (the SCADA added the field before bumping the label).
- 2024-12-31: layout.lite:003 whose relay configs are labelled
  relay.actor.config:002 without StateType.
"""

import json
from pathlib import Path

import pytest

from gjk.sema import SemaCodec
from gjk.sema.types.old_versions.layout_lite_001 import LayoutLite001
from gjk.sema.types.old_versions.layout_lite_003 import LayoutLite003

SAMPLES = Path(__file__).parent / "data" / "sample_messages" / "ops498"


@pytest.mark.parametrize(
    ("name", "cls"),
    [
        ("beech-layout.lite-001-2024-12-03-maxewtf-under-000.json", LayoutLite001),
        ("beech-layout.lite-003-2024-12-31-no-statetype.json", LayoutLite003),
    ],
)
def test_load_mism_layouts_decode(name, cls):
    payload = json.loads((SAMPLES / name).read_text())
    obj = SemaCodec().from_dict(payload, auto_upgrade=False)
    assert isinstance(obj, cls)


def test_maxewtf_present_under_ha1_params_000():
    payload = json.loads(
        (
            SAMPLES / "beech-layout.lite-001-2024-12-03-maxewtf-under-000.json"
        ).read_text()
    )
    assert payload["Ha1Params"]["Version"] == "000"
    obj = SemaCodec().from_dict(payload, auto_upgrade=False)
    assert obj.ha1_params.max_ewt_f == 170
