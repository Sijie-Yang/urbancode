"""Offline GeoTIFF fixtures: derived write, resample, window, slope, zonal."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

rasterio = pytest.importorskip("rasterio")
from rasterio.transform import from_origin

from urbancode.city import City
from urbancode.imagery.grid import stack_to_reference
from urbancode.imagery.indices import ndvi
from urbancode.imagery.read import read
from urbancode.imagery.stac import windowed_read
from urbancode.imagery.terrain import slope_degrees
from urbancode.imagery.write import write_geotiff


def _write_band(path: Path, array: np.ndarray, *, res: float, crs: str = "EPSG:32648") -> Path:
    transform = from_origin(500000.0, 150000.0, res, res)
    write_geotiff(array, path, transform=transform, crs=crs, band_names=[path.stem])
    return path


def test_derived_ndvi_roundtrip_not_parent(tmp_path: Path, cache_dir: Path) -> None:
    pytest.importorskip("rioxarray")
    from urbancode.imagery.fetch import _write_derived

    red = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    nir = np.array([[3.0, 2.0], [1.0, 6.0]], dtype=np.float32)
    stack = np.stack([red, nir])
    parent_path = tmp_path / "sentinel2.tif"
    write_geotiff(
        stack,
        parent_path,
        transform=from_origin(500000.0, 150000.0, 10, 10),
        crs="EPSG:32648",
        band_names=["B04", "B08"],
    )
    parent = read(parent_path, name="sentinel2")
    expected = ndvi({"red": red, "nir": nir, "B04": red, "B08": nir})
    kwargs = _write_derived(
        "ndvi",
        expected,
        parent,
        processing={"index": "ndvi"},
        dtype=np.float32,
        nodata=float("nan"),
    )
    assert Path(kwargs["path"]).resolve() != parent_path.resolve()

    city = City(place="fixture")
    city.add_layer("sentinel2", parent.data, kind="raster", path=str(parent_path), crs=parent.crs)
    city.add_layer("ndvi", **kwargs)
    out = city.to_dir(tmp_path / "city")
    ndvi_path = out / "layers" / "ndvi.tif"
    sent_path = out / "layers" / "sentinel2.tif"
    assert ndvi_path.exists()
    with rasterio.open(ndvi_path) as src:
        saved = src.read(1)
    with rasterio.open(sent_path) as src:
        parent_saved = src.read(1)
    assert saved.shape == expected.shape
    assert np.allclose(saved, expected, equal_nan=True)
    assert not np.allclose(saved, parent_saved, equal_nan=True)
    verified = City.from_dir(out, verify=True)
    assert "ndvi" in verified


def test_stack_resamples_20m_to_10m(tmp_path: Path) -> None:
    b08 = np.ones((4, 4), dtype=np.float32) * 8
    b11 = np.ones((2, 2), dtype=np.float32) * 11
    p08 = _write_band(tmp_path / "B08.tif", b08, res=10)
    p11 = _write_band(tmp_path / "B11.tif", b11, res=20)
    dest = tmp_path / "stack.tif"
    stack_to_reference({"B08": p08, "B11": p11}, dest, reference="B08")
    with rasterio.open(dest) as src, rasterio.open(p08) as ref:
        assert src.width == ref.width
        assert src.height == ref.height
        assert src.transform == ref.transform
        assert src.count == 2
        assert src.read(2).shape == src.read(1).shape


def test_windowed_read_does_not_load_full_tile(tmp_path: Path) -> None:
    data = np.arange(100, dtype=np.float32).reshape(10, 10)
    path = tmp_path / "big.tif"
    # 0.1 degree pixels so a 0.2 x 0.2 bbox is 2x2
    transform = from_origin(103.0, 1.3, 0.1, 0.1)
    write_geotiff(data, path, transform=transform, crs="EPSG:4326")
    bbox = (103.15, 1.05, 103.35, 1.25)
    array, win_transform, crs, profile = windowed_read(str(path), bbox, max_pixels=50)
    assert array.size <= 50
    assert array.shape[-2] < 10 or array.shape[-1] < 10
    west, south, east, north = bbox
    # window transform origin should sit near the requested bbox
    assert win_transform.c >= 103.0
    assert profile["width"] * profile["height"] < 100


def test_max_pixels_guard(tmp_path: Path) -> None:
    data = np.ones((20, 20), dtype=np.float32)
    path = tmp_path / "wide.tif"
    write_geotiff(
        data,
        path,
        transform=from_origin(103.0, 1.3, 0.01, 0.01),
        crs="EPSG:4326",
    )
    from urbancode.errors import RasterSizeLimitError

    with pytest.raises(RasterSizeLimitError, match="max_pixels"):
        windowed_read(str(path), (103.0, 1.1, 103.2, 1.3), max_pixels=10)


def test_projected_slope_is_45_degrees(tmp_path: Path) -> None:
    # 10 m pixels; rise 10 m over 10 m -> 45 degrees along rows
    dem = np.array([[0.0, 0.0, 0.0], [10.0, 10.0, 10.0], [20.0, 20.0, 20.0]])
    sl = slope_degrees(dem, resolution=10.0)
    assert sl[1, 1] == pytest.approx(45.0, abs=1.0)


def test_geographic_dem_reprojects_before_slope(tmp_path: Path) -> None:
    pytest.importorskip("rioxarray")
    from urbancode.city import Layer
    from urbancode.imagery.fetch import _dem_in_meters

    dem = np.array([[0.0, 0.0], [30.0, 30.0]], dtype=np.float32)
    path = tmp_path / "geo_dem.tif"
    write_geotiff(
        dem,
        path,
        transform=from_origin(103.8, 1.35, 0.0003, 0.0003),
        crs="EPSG:4326",
    )
    layer = read(path, name="dem")
    projected, res_m, work_crs = _dem_in_meters(layer)
    assert res_m > 1.0  # metres, not degrees
    assert not getattr(work_crs, "is_geographic", False)


def test_zonal_reprojects_zones(tmp_path: Path) -> None:
    pytest.importorskip("geopandas")
    from shapely.geometry import box
    import geopandas as gpd
    from urbancode.imagery.zonal import zonal_stats

    data = np.ones((10, 10), dtype=np.float32) * 5
    path = tmp_path / "grid.tif"
    write_geotiff(
        data,
        path,
        transform=from_origin(500000, 150000, 10, 10),
        crs="EPSG:32648",
    )
    from rasterio.warp import transform_bounds

    west, south, east, north = transform_bounds(
        "EPSG:32648", "EPSG:4326", 500000, 149900, 500100, 150000
    )
    zones = gpd.GeoDataFrame(
        geometry=[box(west, south, east, north)],
        crs="EPSG:4326",
    )
    out = zonal_stats(str(path), zones, metrics=("mean",))
    assert out["mean"].iloc[0] == pytest.approx(5.0)


def test_scl_masks_cloud_not_vegetation() -> None:
    from urbancode.imagery.stac import apply_scl_mask

    stack = np.ones((2, 2, 2), dtype=np.float32)
    scl = np.array([[4, 8], [3, 5]], dtype=np.uint8)
    masked = apply_scl_mask(stack, scl)
    assert np.isnan(masked[0, 0, 1])  # SCL 8 cloud
    assert np.isnan(masked[0, 1, 0])  # SCL 3 shadow
    assert masked[0, 0, 0] == 1.0  # SCL 4 vegetation kept
    assert masked[0, 1, 1] == 1.0  # SCL 5 bare kept


def test_mosaic_reprojects_to_single_crs(tmp_path: Path) -> None:
    from urbancode.imagery.stac import mosaic_arrays

    a = np.ones((2, 2), dtype=np.float32)
    b = np.ones((2, 2), dtype=np.float32) * 2
    t_a = from_origin(500000, 150000, 10, 10)
    # Same pocket in lon/lat so the merged UTM canvas stays small.
    t_b = from_origin(105.0, 1.356, 0.0001, 0.0001)
    mosaic, transform, crs = mosaic_arrays(
        [(a, t_a, "EPSG:32648"), (b, t_b, "EPSG:4326")],
        dst_crs="EPSG:32648",
        max_pixels=10_000,
    )
    assert str(crs) in {"EPSG:32648", "32648"} or getattr(crs, "to_epsg", lambda: None)() == 32648
    assert mosaic.size > 0


def test_size_limit_not_swallowed_as_missing(tmp_path: Path) -> None:
    from urbancode.errors import RasterSizeLimitError
    from urbancode.imagery.stac import download_assets_windowed

    data = np.ones((20, 20), dtype=np.float32)
    path = tmp_path / "wide.tif"
    write_geotiff(
        data,
        path,
        transform=from_origin(103.0, 1.3, 0.01, 0.01),
        crs="EPSG:4326",
    )

    class _Asset:
        def __init__(self, href: str) -> None:
            self.href = href

    class _Item:
        assets = {"B08": _Asset(str(path))}

    def _identity(item):
        return item

    import urbancode.imagery.stac as stac_mod

    monkey_sign = stac_mod._sign
    stac_mod._sign = _identity
    try:
        with pytest.raises(RasterSizeLimitError):
            download_assets_windowed(
                [_Item()],
                ["B08"],
                tmp_path / "out",
                (103.0, 1.1, 103.2, 1.3),
                max_pixels=10,
            )
    finally:
        stac_mod._sign = monkey_sign


def test_median_composite_not_implemented() -> None:
    from urbancode.imagery.fetch import fetch

    with pytest.raises(NotImplementedError, match="median"):
        fetch(bbox=(103.9, 1.4, 103.91, 1.41), layers=["sentinel2"], composite="median")


def test_zonal_rejects_bare_numpy() -> None:
    pytest.importorskip("geopandas")
    from urbancode.imagery.zonal import zonal_stats

    class _Zones:
        geometry = []
        crs = None

    with pytest.raises(ValueError, match="georeferenced"):
        zonal_stats(np.ones((3, 3)), _Zones())
