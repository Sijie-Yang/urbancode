"""Geometry-aware maps: real CRS extents, context, no PNG-as-map imshow."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / "examples" / "workflows"
REAL = ROOT / "examples" / "data" / "real"

CITY_CRS = {
    "punggol": "EPSG:32648",
    "kallio": "EPSG:32635",
    "greenwich_village": "EPSG:32618",
}


def test_workflow_scripts_do_not_imshow_map_pngs() -> None:
    offenders = []
    for path in WORKFLOWS.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if re.search(r"imshow\([^)]*imread\([^)]*\.png", text, re.I):
            offenders.append(path.name)
    assert offenders == []


def test_each_real_city_has_streets_buildings_boundary_and_locator() -> None:
    for name in CITY_CRS:
        root = REAL / name
        assert (root / "layers" / "streets.graphml").is_file()
        assert (root / "layers" / "buildings.gpkg").is_file()
        assert (root / "area" / "study_area.gpkg").is_file() or (
            root / "manifest.json"
        ).is_file()
        assert (root / "context" / "locator_boundary.gpkg").is_file()
        assert (root / "layers" / "water.gpkg").is_file()


def test_punggol_has_water_and_parks() -> None:
    root = REAL / "punggol"
    assert (root / "layers" / "water.gpkg").is_file()
    assert (root / "layers" / "parks.gpkg").is_file()


def test_context_files_are_in_checksums() -> None:
    for name in CITY_CRS:
        sha = (REAL / name / "checksums.sha256").read_text(encoding="utf-8")
        assert "layers/water.gpkg" in sha
        assert "context/locator_boundary.gpkg" in sha


def test_lazy_context_materializes_before_draw() -> None:
    pytest.importorskip("geopandas")
    from urbancode.cartography import _layer

    city = __import__("urbancode", fromlist=["load"]).load(
        REAL / "punggol", layers=["streets", "buildings", "water"], lazy=True
    )
    assert city.layers["streets"].data is None
    layer = _layer(city, "streets")
    assert layer is not None
    assert layer.data is not None
    assert city.layers["streets"].lazy is False


def test_punggol_map_extent_is_utm() -> None:
    gpd = pytest.importorskip("geopandas")
    pytest.importorskip("matplotlib")
    from examples.recipes._common import load_punggol

    city = load_punggol(["streets", "buildings", "parks", "water"])
    fig, ax = __import__("matplotlib.pyplot", fromlist=["pyplot"]).subplots()
    city.plot(ax=ax, layers=["streets", "buildings"], show_scale=False, show_north=False, locator=False)
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    assert x0 > 200_000
    assert x1 < 500_000
    assert y0 > 100_000
    assert city.study_area.metric_crs == "EPSG:32648"
    fig.clf()


def test_same_city_panels_share_extent() -> None:
    pytest.importorskip("geopandas")
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    from examples.recipes._common import load_punggol
    from urbancode.cartography import apply_map_extent, metric_crs

    city = load_punggol(["streets"])
    fig, axes = plt.subplots(1, 2)
    crs = metric_crs(city)
    apply_map_extent(axes[0], city, crs)
    apply_map_extent(axes[1], city, crs)
    assert axes[0].get_xlim() == axes[1].get_xlim()
    assert axes[0].get_ylim() == axes[1].get_ylim()
    plt.close(fig)


def test_kallio_and_greenwich_metric_crs() -> None:
    pytest.importorskip("geopandas")
    from examples.recipes._common import load_pocket

    kallio = load_pocket("kallio", layers=["streets"])
    nyc = load_pocket("greenwich_village", layers=["streets"])
    assert kallio.study_area.metric_crs == "EPSG:32635"
    assert nyc.study_area.metric_crs == "EPSG:32618"


def test_missing_cells_default_is_not_solid_grey() -> None:
    from urbancode.cartography import pop_carto

    carto = pop_carto({})
    assert carto["missing_style"] == "transparent"


def test_workflow_captions_name_city_and_units() -> None:
    docs = ROOT / "docs" / "source" / "workflows"
    required = {
        "green_accessibility.rst": ("Punggol", "250 m", "EPSG:32648"),
        "heat_exposure.rst": ("Punggol", "250 m"),
        "punggol_urban_profile.rst": ("Punggol", "250 m"),
        "street_experience.rst": ("Punggol",),
        "multi_city_comparison.rst": ("Punggol", "Kallio", "Greenwich"),
    }
    missing = []
    for name, tokens in required.items():
        text = (docs / name).read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                missing.append(f"{name}: {token}")
    assert missing == []
