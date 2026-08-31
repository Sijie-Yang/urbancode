from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import urbancode as uc
from urbancode.city import City, Layer, load
from urbancode.imagery.indices import ndvi
from urbancode.imagery.terrain import hillshade, slope, slope_degrees
from urbancode.imagery.write import write_geotiff


def test_load_and_save_aliases(tmp_path: Path) -> None:
    city = City(place="A")
    city.add_layer("scores", pd.DataFrame({"v": [1]}), kind="table")
    out = city.save(tmp_path / "city")
    loaded = load(out)
    assert loaded.place == "A"
    assert list(loaded["scores"]["v"]) == [1]
    assert uc.load(out).place == "A"


def test_ndvi_bandmap_still_returns_array() -> None:
    red = np.array([[1.0, 2.0], [3.0, 4.0]])
    nir = np.array([[3.0, 2.0], [1.0, 6.0]])
    out = ndvi({"nir": nir, "red": red})
    assert isinstance(out, np.ndarray)
    assert np.allclose(out, (nir - red) / (nir + red))


def test_ndvi_path_returns_layer(tmp_path: Path) -> None:
    pytest.importorskip("rasterio")
    from rasterio.transform import Affine

    red = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    nir = np.array([[3.0, 2.0], [1.0, 6.0]], dtype=np.float32)
    path = tmp_path / "s2.tif"
    write_geotiff(
        np.stack([red, nir]),
        path,
        transform=Affine(10.0, 0.0, 0.0, 0.0, -10.0, 20.0),
        crs="EPSG:32648",
        band_names=["B04", "B08"],
    )
    layer = ndvi(path)
    assert isinstance(layer, Layer)
    assert layer.kind == "raster"
    assert layer.crs is not None
    assert layer.metadata.get("transform") is not None
    expected = (nir.astype(float) - red) / (nir.astype(float) + red)
    assert np.allclose(layer.data, expected)


def test_slope_and_hillshade_inherit_grid(tmp_path: Path) -> None:
    pytest.importorskip("rasterio")
    from rasterio.transform import Affine

    dem = np.array([[0.0, 0.0], [10.0, 10.0]], dtype=np.float32)
    path = tmp_path / "dem.tif"
    write_geotiff(
        dem,
        path,
        transform=Affine(10.0, 0.0, 0.0, 0.0, -10.0, 20.0),
        crs="EPSG:32648",
    )
    slope_layer = slope(path)
    shade = hillshade(path)
    assert isinstance(slope_layer, Layer)
    assert isinstance(shade, Layer)
    assert slope_layer.metadata["processing"]["op"] == "slope"
    assert np.allclose(slope_layer.data, slope_degrees(dem, 10.0))


def test_zonal_stats_layer_no_temp_file(tmp_path: Path) -> None:
    pytest.importorskip("rasterio")
    pytest.importorskip("geopandas")
    from shapely.geometry import box
    import geopandas as gpd
    from rasterio.transform import Affine

    data = np.ones((10, 10), dtype=np.float32) * 5
    path = tmp_path / "grid.tif"
    transform = Affine(10.0, 0.0, 500000.0, 0.0, -10.0, 150000.0)
    write_geotiff(
        data,
        path,
        transform=transform,
        crs="EPSG:32648",
        band_names=["B04"],
    )
    stack = np.stack([data, data * 3])
    s2 = tmp_path / "s2.tif"
    write_geotiff(
        stack,
        s2,
        transform=transform,
        crs="EPSG:32648",
        band_names=["B04", "B08"],
    )
    ndvi_layer = ndvi(s2)
    zones = gpd.GeoDataFrame(
        geometry=[box(500000, 149900, 500100, 150000)],
        crs="EPSG:32648",
    )
    stats = uc.imagery.zonal_stats(ndvi_layer, zones, metrics=["mean"])
    assert isinstance(stats, Layer)
    assert stats.kind == "vector"
    assert stats.data["mean"].iloc[0] == pytest.approx(0.5)


def test_layer_plot_saves_png(tmp_path: Path) -> None:
    gpd = pytest.importorskip("geopandas")
    pytest.importorskip("matplotlib")
    from shapely.geometry import Point

    gdf = gpd.GeoDataFrame({"v": [1]}, geometry=[Point(103.9, 1.4)], crs="EPSG:4326")
    layer = Layer(name="pois", kind="vector", data=gdf, crs="EPSG:4326")
    out = layer.plot(title="t", save=tmp_path / "p.png")
    assert Path(out).is_file()
    assert Path(out).stat().st_size > 0


def test_centrality_and_accessibility_return_layer() -> None:
    nx = pytest.importorskip("networkx")
    graph = nx.Graph()
    graph.add_node(1, x=103.90, y=1.40)
    graph.add_node(2, x=103.91, y=1.40)
    graph.add_node(3, x=103.91, y=1.41)
    graph.add_edge(1, 2, length=100.0)
    graph.add_edge(2, 3, length=100.0)
    result = uc.network.centrality(graph, metric="betweenness")
    assert isinstance(result, Layer)
    assert result.kind == "graph"
    assert result.metadata["column"] == "betweenness"
    access = uc.network.accessibility(graph, radius=150, metric="reachability")
    assert access.metadata["column"] == "reachability"
    assert access.data.nodes[2]["reachability"] >= 1


def test_layer_save_raster(tmp_path: Path) -> None:
    pytest.importorskip("rasterio")

    array = np.array([[0.1, 0.2], [0.3, 0.4]])
    layer = Layer(
        name="ndvi",
        kind="raster",
        data=array,
        crs="EPSG:32648",
        metadata={"transform": [10.0, 0.0, 0.0, 0.0, -10.0, 20.0], "nodata": float("nan")},
    )
    dest = layer.save(tmp_path / "ndvi.tif")
    assert dest.is_file()
