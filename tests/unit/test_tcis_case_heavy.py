from __future__ import annotations

import pytest


@pytest.mark.live
@pytest.mark.heavy
def test_thermal_affordance_on_one_licensed_photo() -> None:
    pytest.importorskip("torch")
    pytest.importorskip("geopandas")
    import urbancode as uc
    from examples.research_cases._tcis_data import tiny_catalog

    frame = tiny_catalog().head(1)
    images = uc.images.from_table(
        frame,
        view_type="streetview",
        city_id="punggol",
        source="wikimedia-commons",
        license="CC BY-SA 4.0",
    )
    result = uc.perception.thermal_affordance(images, device="cpu")
    assert "thermal_affordance" in result.data.columns
    assert result.data["thermal_affordance"].notna().any()
