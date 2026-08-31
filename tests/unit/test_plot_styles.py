"""Indicator color-scale contracts. No NDVI range on other units."""

from __future__ import annotations

import numpy as np
import pytest

from urbancode.plot import NDVI_VMIN, NDVI_VMAX, indicator_style


def test_ndvi_keeps_fixed_range() -> None:
    spec = indicator_style("ndvi", unit="dimensionless", values=[-0.1, 0.4, 0.7])
    assert spec["vmin"] == NDVI_VMIN
    assert spec["vmax"] == NDVI_VMAX
    assert spec["cmap"] == "RdYlGn"


def test_park_distance_is_not_ndvi_scale() -> None:
    spec = indicator_style("park_near_m", unit="metre", values=[12.0, 80.0, 240.0])
    assert spec["vmin"] != NDVI_VMIN or spec["vmax"] != NDVI_VMAX
    assert spec["vmax"] >= 80.0
    assert "m" in spec["label"]
    assert spec["cmap"] != "RdYlGn"


def test_reachability_is_node_count() -> None:
    spec = indicator_style("reachability", unit="count", values=[2.0, 8.0, 21.0])
    assert spec["vmin"] == 0.0
    assert spec["vmax"] >= 8.0
    assert spec["vmin"] != NDVI_VMIN
    assert spec["vmax"] != NDVI_VMAX
    assert "count" in spec["label"]


def test_fraction_is_zero_one() -> None:
    spec = indicator_style("park_frac", unit="area_fraction", values=[0.1, 0.4, 0.9])
    assert spec["vmin"] == 0.0
    assert spec["vmax"] == 1.0


def test_explicit_vmin_vmax_override() -> None:
    spec = indicator_style("reachability", values=[1, 2, 3], vmin=5, vmax=9, cmap="plasma")
    assert spec["vmin"] == 5
    assert spec["vmax"] == 9
    assert spec["cmap"] == "plasma"


def test_constant_field_is_labelled() -> None:
    spec = indicator_style("air_temperature", unit="degree_celsius", values=[31.2, 31.2, 31.2])
    assert spec["constant"] is True
    assert "constant field" in spec["label"]
    assert spec["vmin"] < spec["vmax"]


def test_utci_uses_celsius() -> None:
    spec = indicator_style("utci", unit="degree_celsius", values=[28.0, 32.0, 35.0])
    assert "°C" in spec["label"]
    assert spec["cmap"] == "RdYlBu_r"
    assert spec["vmin"] != NDVI_VMIN


def test_vector_plot_uses_style(tmp_path) -> None:
    gpd = pytest.importorskip("geopandas")
    pytest.importorskip("matplotlib")
    from shapely.geometry import box

    from urbancode.city import Layer

    gdf = gpd.GeoDataFrame(
        {"value": [10.0, 80.0, 200.0]},
        geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1), box(2, 0, 3, 1)],
        crs="EPSG:32648",
    )
    layer = Layer(
        name="park_near_m",
        kind="vector",
        data=gdf,
        crs="EPSG:32648",
        metadata={"column": "value", "unit": "metre"},
    )
    out = layer.plot(save=tmp_path / "park.png")
    assert out.is_file()
    spec = indicator_style("park_near_m", unit="metre", values=gdf["value"])
    assert spec["vmax"] >= 80
