from __future__ import annotations

from pathlib import Path

import pytest

from .helpers import load_offline
from .png_checks import assert_gallery_png

pytestmark = pytest.mark.gallery_imagery


def test_ndvi_map(tmp_path: Path) -> None:
    pytest.importorskip("rasterio")
    pytest.importorskip("matplotlib")
    result = load_offline("03_ndvi_map.py").main(tmp_path, add_basemap=False)
    assert_gallery_png(result["figure"])


def test_terrain_hillshade(tmp_path: Path) -> None:
    pytest.importorskip("rasterio")
    pytest.importorskip("matplotlib")
    result = load_offline("04_terrain_hillshade.py").main(tmp_path, add_basemap=False)
    assert_gallery_png(result["figure"])


def test_zonal_ndvi(tmp_path: Path) -> None:
    pytest.importorskip("rasterio")
    pytest.importorskip("geopandas")
    pytest.importorskip("matplotlib")
    result = load_offline("05_zonal_ndvi.py").main(tmp_path, add_basemap=False)
    assert_gallery_png(result["figure"])
    assert Path(result["table"]).is_file()
