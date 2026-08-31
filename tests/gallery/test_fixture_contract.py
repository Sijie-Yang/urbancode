"""Semantic checks on the canonical Punggol City fixture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .helpers import BBOX, FIXTURE, TITLE

WEST, SOUTH, EAST, NORTH = BBOX


def _manifest() -> dict:
    return json.loads((FIXTURE / "manifest.json").read_text(encoding="utf-8"))


def _dataset() -> dict:
    return json.loads((FIXTURE / "dataset.json").read_text(encoding="utf-8"))


def test_manifest_paths_are_relative() -> None:
    for record in _manifest()["layers"]:
        rel = record.get("path")
        assert rel, record
        path = Path(rel)
        assert not path.is_absolute(), rel
        assert ".." not in path.parts, rel
        assert rel.startswith("layers/"), rel
        assert (FIXTURE / rel).is_file(), rel


def test_fixture_metadata_contract() -> None:
    meta = _dataset()
    assert meta["city_id"] == "punggol"
    assert "Punggol" in meta["place"]
    assert meta["bbox"] == list(BBOX)
    assert meta["geographic_crs"] == "EPSG:4326"
    assert meta["metric_crs"] == "EPSG:32648"
    assert meta["generated_by"] == "scripts/data/build_real_pockets.py"
    assert meta["synthetic"] is False
    assert (FIXTURE / "LICENSE.md").is_file()
    assert TITLE in (FIXTURE / "LICENSE.md").read_text(encoding="utf-8")
    assert _manifest()["place"] == TITLE


@pytest.mark.gallery_network
def test_vector_crs_types_and_bbox() -> None:
    gpd = pytest.importorskip("geopandas")
    buildings = gpd.read_file(FIXTURE / "layers" / "buildings.gpkg")
    parks = gpd.read_file(FIXTURE / "layers" / "parks.gpkg")
    pois = gpd.read_file(FIXTURE / "layers" / "pois.gpkg")
    for frame, geom in (
        (buildings, "Polygon"),
        (parks, "Polygon"),
        (pois, "Point"),
    ):
        assert frame.crs is not None
        assert frame.crs.to_string() == "EPSG:4326"
        assert frame.geom_type.str.contains(geom).all()
        minx, miny, maxx, maxy = frame.total_bounds
        assert minx >= WEST - 1e-3
        assert miny >= SOUTH - 1e-3
        assert maxx <= EAST + 1e-3
        assert maxy <= NORTH + 1e-3


@pytest.mark.gallery_network
def test_from_dir_uses_city_contract() -> None:
    pytest.importorskip("geopandas")
    pytest.importorskip("networkx")
    import urbancode as uc

    city = uc.City.from_dir(FIXTURE)
    assert city.place == TITLE
    for name in ("streets", "buildings", "parks", "pois", "water"):
        assert name in city
    for record in _manifest()["layers"]:
        layer = city.layer(record["name"])
        assert layer.kind == record["kind"]
        assert Path(layer.path).is_relative_to(FIXTURE.resolve()) or Path(
            str(layer.path)
        ).resolve().is_relative_to(FIXTURE.resolve())


@pytest.mark.gallery_imagery
def test_sentinel_and_dem_grid() -> None:
    rasterio = pytest.importorskip("rasterio")
    sentinel = FIXTURE / "layers" / "sentinel2.tif"
    dem = FIXTURE / "layers" / "dem.tif"
    with rasterio.open(sentinel) as src:
        assert list(src.descriptions) == ["B02", "B03", "B04", "B08", "B11"]
        assert src.crs.to_string() == "EPSG:32648"
        assert src.count == 5
        assert abs(src.transform.a) == pytest.approx(10.0)
        assert abs(src.transform.e) == pytest.approx(10.0)
        red = src.read(3)
        nir = src.read(4)
        transform = src.transform
        shape = src.shape
        nodata = src.nodata
    with rasterio.open(dem) as src:
        assert src.crs.to_string() == "EPSG:32648"
        assert src.shape == shape
        assert src.transform == transform
        elevation = src.read(1)
        import numpy as np

        assert float(np.nanstd(elevation)) > 0.0
    denom = nir + red
    ndvi = (nir - red) / denom
    assert float(ndvi.max()) > 0.3
    assert float(ndvi.min()) < 0.1
    assert nodata is None or (isinstance(nodata, float))
