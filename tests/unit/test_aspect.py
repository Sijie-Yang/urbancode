from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from urbancode.city import Layer
from urbancode.imagery.terrain import aspect, aspect_degrees
from urbancode.imagery.write import write_geotiff


def _dem_layer(array: np.ndarray, *, crs="EPSG:32648", transform=None, nodata=None) -> Layer:
    if transform is None:
        transform = [10.0, 0.0, 0.0, 0.0, -10.0, 30.0]
    return Layer(
        name="dem",
        kind="raster",
        data=np.asarray(array, dtype=float),
        crs=crs,
        metadata={"transform": transform, "nodata": nodata},
    )


def _center(layer: Layer) -> float:
    values = np.asarray(layer.data)
    return float(values[values.shape[0] // 2, values.shape[1] // 2])


def test_aspect_cardinal_ramps() -> None:
    pytest.importorskip("rasterio")
    north = _dem_layer([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0]])
    east = _dem_layer([[2.0, 1.0, 0.0], [2.0, 1.0, 0.0], [2.0, 1.0, 0.0]])
    south = _dem_layer([[2.0, 2.0, 2.0], [1.0, 1.0, 1.0], [0.0, 0.0, 0.0]])
    west = _dem_layer([[0.0, 1.0, 2.0], [0.0, 1.0, 2.0], [0.0, 1.0, 2.0]])
    assert _center(aspect(north)) == pytest.approx(0.0, abs=1e-6)
    assert _center(aspect(east)) == pytest.approx(90.0, abs=1e-6)
    assert _center(aspect(south)) == pytest.approx(180.0, abs=1e-6)
    assert _center(aspect(west)) == pytest.approx(270.0, abs=1e-6)


def test_aspect_flat_and_nodata() -> None:
    pytest.importorskip("rasterio")
    flat = aspect(_dem_layer(np.ones((3, 3)) * 5.0))
    assert np.all(np.isnan(flat.data))

    dem = np.array([[0.0, 0.0, 0.0], [1.0, -9999.0, 1.0], [2.0, 2.0, 2.0]])
    layer = aspect(_dem_layer(dem, nodata=-9999.0))
    assert np.isnan(layer.data[1, 1])


def test_aspect_rejects_geographic_crs() -> None:
    pytest.importorskip("rasterio")
    dem = _dem_layer([[0.0, 1.0], [2.0, 3.0]], crs="EPSG:4326")
    with pytest.raises(ValueError, match="geographic"):
        aspect(dem)
    missing = _dem_layer([[0.0, 1.0], [2.0, 3.0]], crs=None)
    with pytest.raises(ValueError, match="projected CRS"):
        aspect(missing)


def test_aspect_nonsquare_pixels_and_grid_inheritance(tmp_path) -> None:
    pytest.importorskip("rasterio")
    from rasterio.transform import Affine

    diagonal = np.array([[0.0, 1.0, 2.0], [1.0, 2.0, 3.0], [2.0, 3.0, 4.0]])
    square = aspect(_dem_layer(diagonal, transform=[10.0, 0.0, 0.0, 0.0, -10.0, 30.0]))
    stretched = aspect(_dem_layer(diagonal, transform=[20.0, 0.0, 0.0, 0.0, -10.0, 30.0]))
    assert _center(square) != pytest.approx(_center(stretched), abs=1e-3)

    path = tmp_path / "dem.tif"
    write_geotiff(
        np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0]], dtype=np.float32),
        path,
        transform=Affine(10.0, 0.0, 500000.0, 0.0, -10.0, 150000.0),
        crs="EPSG:32648",
    )
    parent = Layer(
        name="dem",
        kind="raster",
        data=None,
        path=str(path),
        crs="EPSG:32648",
        metadata={"transform": [10.0, 0.0, 500000.0, 0.0, -10.0, 150000.0]},
    )
    layer = aspect(parent)
    assert layer.crs is not None
    assert "32648" in str(layer.crs)
    assert layer.metadata["transform"][0] == pytest.approx(10.0)
    assert layer.metadata["transform"][4] == pytest.approx(-10.0)
    assert layer.metadata["unit"] == "degree"
    assert layer.metadata["convention"] == "degrees_clockwise_from_north"
    assert layer.metadata["processing"]["op"] == "aspect"
    assert np.isnan(layer.metadata["nodata"])


def test_aspect_on_fixture() -> None:
    pytest.importorskip("rasterio")
    fixture = Path(__file__).resolve().parents[2] / "examples" / "data" / "punggol_pocket"
    if not fixture.is_dir():
        pytest.skip("punggol fixture missing")
    import urbancode as uc

    layer = uc.imagery.aspect(uc.load(fixture, lazy=True)["dem"])
    assert layer.metadata["unit"] == "degree"
    assert layer.metadata["processing"]["op"] == "aspect"
    assert layer.data.shape[0] > 1


def test_aspect_degrees_array_api() -> None:
    dem = np.array([[0.0, 0.0], [10.0, 10.0]])
    asp = aspect_degrees(dem, resolution=10.0)
    assert asp.shape == (2, 2)
    assert asp.min() >= 0
    with pytest.raises(TypeError, match="resolution"):
        aspect(dem)
