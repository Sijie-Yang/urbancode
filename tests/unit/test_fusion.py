from __future__ import annotations

from pathlib import Path

import pytest

gpd = pytest.importorskip("geopandas")
pytest.importorskip("rasterio")
pytest.importorskip("networkx")
pytest.importorskip("shapely")

import urbancode as uc
from urbancode.area import StudyArea
from urbancode.provenance import is_missing

FIXTURE = Path(__file__).resolve().parents[2] / "examples" / "data" / "real" / "punggol"


def test_grid_rejects_geographic_metric_crs() -> None:
    area = StudyArea.from_bbox(103.905, 1.4, 103.915, 1.41, place="Punggol")
    city = uc.City(area)
    city.metadata["bbox"] = list(area.bbox)
    with pytest.raises(ValueError, match="projected"):
        uc.units.grid(city, cell_size=250, metric_crs="EPSG:4326")


def test_ndvi_and_reachability_share_unit_ids() -> None:
    city = uc.load(FIXTURE, layers=["streets", "sentinel2"], lazy=True)
    area = StudyArea.from_bbox(*city.metadata["bbox"], place=city.place)
    city.study_area = area
    units = uc.units.grid(city, cell_size=250)
    assert units.unit_ids
    assert units.metric_crs == "EPSG:32648"

    ndvi = uc.imagery.ndvi(city.layers["sentinel2"].path)
    reach = uc.network.accessibility(city["streets"], radius=150, metric="reachability")

    ndvi_result = uc.fusion.aggregate(ndvi, units, stat="mean", indicator="ndvi")
    reach_result = uc.fusion.aggregate(reach, units, stat="mean", indicator="reachability")

    assert {r.unit_id for r in ndvi_result.records} == set(units.unit_ids)
    assert {r.unit_id for r in reach_result.records} == set(units.unit_ids)
    assert all(r.coverage is not None for r in ndvi_result.records)
    assert all(r.coverage is not None for r in reach_result.records)

    missing = [r for r in ndvi_result.records if r.value is None]
    for rec in missing:
        assert rec.value != 0
        assert is_missing(rec.value) or rec.value is None

    filled = [r for r in ndvi_result.records if r.value is not None]
    assert filled, "expected at least one NDVI cell with data"
    assert any(r.value is not None for r in reach_result.records)
    for rec in ndvi_result.records:
        if rec.coverage is not None:
            assert 0.0 <= rec.coverage <= 1.0
    combined = uc.fusion.combine(units, ndvi_result, reach_result)
    names = {r.indicator for r in combined.records}
    assert "ndvi" in names and "reachability" in names


def test_combine_rejects_mismatched_city() -> None:
    area = StudyArea.from_bbox(103.905, 1.4, 103.915, 1.41, place="Punggol")
    city = uc.City(area)
    city.metadata["bbox"] = list(area.bbox)
    units = uc.units.grid(city, cell_size=250)
    other = uc.IndicatorResult(
        records=[
            uc.IndicatorRecord("nyc", units.unit_ids[0], "ndvi", 0.1),
        ]
    )
    with pytest.raises(ValueError, match="city_id"):
        uc.fusion.combine(units, other)


def test_aggregate_points_polygons_and_edges() -> None:
    city = uc.load(FIXTURE, layers=["streets", "parks"], lazy=True)
    area = StudyArea.from_bbox(*city.metadata["bbox"], place=city.place)
    city.study_area = area
    units = uc.units.grid(city, cell_size=250)
    parks = uc.fusion.aggregate(
        city.layers["parks"], units, stat="area_fraction", indicator="park_fraction"
    )
    assert {r.unit_id for r in parks.records} == set(units.unit_ids)
    import pandas as pd

    lon = (area.bbox[0] + area.bbox[2]) / 2.0
    lat = (area.bbox[1] + area.bbox[3]) / 2.0
    catalog = pd.DataFrame({"colorfulness": [0.4], "lon": [lon], "lat": [lat]})
    points = uc.streetview.as_layer(catalog)
    color = uc.fusion.aggregate(
        points, units, stat="mean", column="colorfulness", indicator="color"
    )
    assert any(r.value is not None for r in color.records)
    table = uc.fusion.aggregate(
        catalog,
        units,
        stat="count",
        indicator="sv_count",
    )
    assert any((r.value or 0) > 0 for r in table.records)
    edges = uc.fusion.aggregate(
        city.layers["streets"],
        units,
        stat="count",
        indicator="edge_count",
        part="edges",
    )
    assert {r.unit_id for r in edges.records} == set(units.unit_ids)
    with pytest.raises(ValueError, match="unknown stat"):
        uc.fusion.aggregate(points, units, stat="kurtosis")
    with pytest.raises(KeyError, match="missing"):
        uc.fusion.aggregate(
            points, units, stat="mean", column="not_a_column", indicator="missing"
        )


def test_grid_ids_use_world_origin() -> None:
    area = StudyArea.from_bbox(103.905, 1.4, 103.915, 1.41, place="Punggol")
    city = uc.City(area)
    city.metadata["bbox"] = list(area.bbox)
    units = uc.units.grid(city, cell_size=250)
    assert all(uid.startswith("grid:EPSG:32648:250:") for uid in units.unit_ids)
    assert "unit_type" in units.frame.columns
    shifted = StudyArea.from_bbox(103.906, 1.401, 103.916, 1.411, place="Punggol")
    other = uc.City(shifted)
    other.metadata["bbox"] = list(shifted.bbox)
    other_units = uc.units.grid(other, cell_size=250)
    assert set(units.unit_ids) & set(other_units.unit_ids)
