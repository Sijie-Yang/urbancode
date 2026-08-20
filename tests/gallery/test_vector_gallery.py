from __future__ import annotations

from pathlib import Path

import pytest

from .helpers import load_offline
from .png_checks import assert_gallery_png

pytestmark = pytest.mark.gallery_network


def test_streets_buildings(tmp_path: Path) -> None:
    pytest.importorskip("geopandas")
    pytest.importorskip("matplotlib")
    result = load_offline("01_streets_buildings.py").main(tmp_path, add_basemap=False)
    assert_gallery_png(result["figure"])


def test_parks_pois(tmp_path: Path) -> None:
    pytest.importorskip("geopandas")
    pytest.importorskip("matplotlib")
    result = load_offline("02_parks_pois.py").main(tmp_path, add_basemap=False)
    assert_gallery_png(result["figure"])
