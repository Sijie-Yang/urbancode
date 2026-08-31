from __future__ import annotations

from pathlib import Path

from .helpers import GALLERY_STATIC
from .png_checks import assert_gallery_png

FIGURES = (
    "01_streets_buildings.png",
    "02_parks_pois.png",
    "03_ndvi.png",
    "04_terrain.png",
    "05_zonal_ndvi.png",
    "06_access.png",
    "07_streetview_results.png",
)

TUTORIALS = Path(__file__).resolve().parents[2] / "docs" / "source" / "_static" / "tutorials"
TUTORIAL_FIGURES = (
    "network_streets.png",
    "network_buildings.png",
    "network_streets_buildings.png",
    "network_parks_pois.png",
    "network_streets_parks.png",
    "network_betweenness.png",
    "network_closeness.png",
    "network_reachability.png",
    "network_clustering.png",
    "network_efficiency.png",
    "imagery_ndvi.png",
    "imagery_ndbi.png",
    "imagery_hillshade.png",
    "imagery_slope.png",
    "imagery_aspect.png",
    "imagery_terrain.png",
    "imagery_zonal_ndvi.png",
    "streetview_photo.png",
    "streetview_panel.png",
)


def test_committed_gallery_pngs() -> None:
    for name in FIGURES:
        assert_gallery_png(GALLERY_STATIC / name)


def test_committed_tutorial_pngs() -> None:
    for name in TUTORIAL_FIGURES:
        assert_gallery_png(TUTORIALS / name)
