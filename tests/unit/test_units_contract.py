from __future__ import annotations

import pytest

gpd = pytest.importorskip("geopandas")
pytest.importorskip("shapely")

from shapely.geometry import box

from urbancode.area import StudyArea
from urbancode.city import City
from urbancode.units import from_layer, grid, hexgrid


def test_from_bbox_projected_crs() -> None:
    area = StudyArea.from_bbox(
        380000,
        155000,
        381000,
        156000,
        crs="EPSG:32648",
        place="Projected",
    )
    assert abs(area.bbox[0]) <= 180
    assert area.metric_crs == "EPSG:32648"


def test_from_geometry_projected_roundtrip() -> None:
    frame = gpd.GeoDataFrame(
        geometry=[box(380000, 155000, 381000, 156000)],
        crs="EPSG:32648",
    )
    area = StudyArea.from_geometry(frame, place="Projected")
    assert area.bbox is not None
    assert abs(area.bbox[0]) <= 180
    assert area.metric_crs == "EPSG:32648"


def test_hexgrid_has_stable_ids() -> None:
    area = StudyArea.from_bbox(103.905, 1.4, 103.915, 1.41, place="Punggol")
    city = City(area)
    city.metadata["bbox"] = list(area.bbox)
    units = hexgrid(city, cell_size=250)
    assert units.kind == "hexgrid"
    assert units.unit_ids
    assert all(i.startswith("hex:") for i in units.unit_ids)


@pytest.mark.parametrize("constructor", [grid, hexgrid])
def test_regular_units_are_clipped_to_study_envelope(constructor) -> None:
    area = StudyArea.from_bbox(103.905, 1.4, 103.915, 1.41, place="Punggol")
    city = City(area)
    city.metadata["bbox"] = list(area.bbox)

    units = constructor(city, cell_size=250)
    envelope = gpd.GeoDataFrame(
        geometry=[box(*area.bbox)], crs="EPSG:4326"
    ).to_crs(units.metric_crs).geometry.iloc[0]

    union = units.frame.geometry.union_all()
    assert union.difference(envelope).area == pytest.approx(0.0, abs=1e-6)
    assert any(geom.area < 250 * 250 for geom in units.frame.geometry)


def test_from_layer_polygons() -> None:
    frame = gpd.GeoDataFrame(
        {"name": ["a"]},
        geometry=[box(378000, 154000, 378200, 154200)],
        crs="EPSG:32648",
    )
    units = from_layer(frame, id_column="name", city_id="punggol")
    assert units.unit_ids == ["a"]


def test_from_layer_fingerprint_survives_reorder() -> None:
    from shapely.geometry import box

    frame = gpd.GeoDataFrame(
        geometry=[box(0, 0, 10, 10), box(20, 20, 30, 30)],
        crs="EPSG:32648",
    )
    first = from_layer(frame, city_id="punggol")
    second = from_layer(frame.iloc[::-1].reset_index(drop=True), city_id="punggol")
    assert set(first.unit_ids) == set(second.unit_ids)
    assert all(i.startswith("geom:v1:") for i in first.unit_ids)
    assert first.metadata["fingerprint"] == "geom.v1"


def test_from_layer_fingerprint_ignores_ring_and_part_order() -> None:
    from shapely.geometry import MultiPolygon, Polygon, box

    poly = box(0, 0, 10, 10)
    reversed_ring = Polygon(list(poly.exterior.coords)[::-1])
    multi_a = MultiPolygon([box(0, 0, 4, 4), box(6, 6, 10, 10)])
    multi_b = MultiPolygon([box(6, 6, 10, 10), box(0, 0, 4, 4)])
    first = from_layer(
        gpd.GeoDataFrame(geometry=[poly, multi_a], crs="EPSG:32648"),
        city_id="punggol",
    )
    second = from_layer(
        gpd.GeoDataFrame(geometry=[reversed_ring, multi_b], crs="EPSG:32648"),
        city_id="punggol",
    )
    assert first.unit_ids == second.unit_ids


def test_from_layer_duplicate_geometry_raises() -> None:
    frame = gpd.GeoDataFrame(
        geometry=[box(0, 0, 10, 10), box(0, 0, 10, 10)],
        crs="EPSG:32648",
    )
    with pytest.raises(ValueError, match="duplicate"):
        from_layer(frame, city_id="punggol")


def test_from_layer_roundtrip_gpkg(tmp_path) -> None:
    frame = gpd.GeoDataFrame(
        geometry=[box(0, 0, 10, 10), box(20, 20, 30, 30)],
        crs="EPSG:32648",
    )
    first = from_layer(frame, city_id="punggol")
    path = tmp_path / "units.gpkg"
    first.frame.to_file(path, driver="GPKG")
    loaded = gpd.read_file(path)
    second = from_layer(loaded.drop(columns=["unit_id"]), city_id="punggol")
    assert set(first.unit_ids) == set(second.unit_ids)
