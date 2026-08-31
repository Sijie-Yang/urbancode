from __future__ import annotations

import pandas as pd
import pytest

gpd = pytest.importorskip("geopandas")

import urbancode as uc
from urbancode.area import StudyArea


def test_aggregate_many_returns_indicator_result() -> None:
    area = StudyArea.from_bbox(103.905, 1.4, 103.915, 1.41, place="Punggol")
    city = uc.City(area)
    city.metadata["bbox"] = list(area.bbox)
    units = uc.units.grid(city, cell_size=250)
    lon = (area.bbox[0] + area.bbox[2]) / 2.0
    lat = (area.bbox[1] + area.bbox[3]) / 2.0
    frame = pd.DataFrame(
        {
            "image_id": ["p1"],
            "image_path": ["p1.jpg"],
            "longitude": [lon],
            "latitude": [lat],
            "thermal_affordance": [3.4],
            "shading_area": [2.1],
            "greenery_rate": [1.8],
        }
    )
    points = uc.images.from_table(frame, view_type="streetview", city_id="punggol")
    result = uc.fusion.aggregate_many(
        points,
        units,
        columns={
            "thermal_affordance": {
                "indicator": "thermal_affordance",
                "unit": "score_0_5",
            },
            "shading_area": {"indicator": "perceived_shading", "unit": "score_0_5"},
            "greenery_rate": {"indicator": "perceived_greenery", "unit": "score_0_5"},
        },
        stat="mean",
    )
    names = {rec.indicator for rec in result.records}
    assert names == {"thermal_affordance", "perceived_shading", "perceived_greenery"}
    assert {rec.unit_id for rec in result.records} == set(units.unit_ids)
    assert result.metadata["op"] == "aggregate_many"
    filled = [rec for rec in result.records if rec.value is not None]
    assert filled
    assert any(rec.indicator == "thermal_affordance" and rec.unit == "score_0_5" for rec in filled)
    empty = [rec for rec in result.records if rec.value is None]
    assert empty
    assert all(rec.value is None for rec in empty)
