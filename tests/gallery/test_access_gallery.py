from __future__ import annotations

from pathlib import Path

import pytest

from .helpers import load_offline
from .png_checks import assert_gallery_png

pytestmark = pytest.mark.gallery_network


def test_access_radius(tmp_path: Path) -> None:
    pytest.importorskip("networkx")
    pytest.importorskip("matplotlib")
    result = load_offline("06_access_radius.py").main(tmp_path, add_basemap=False)
    assert_gallery_png(result["figure"])
