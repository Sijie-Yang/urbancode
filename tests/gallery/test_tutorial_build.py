from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from .png_checks import assert_gallery_png

pytestmark = pytest.mark.gallery_imagery

REPO = Path(__file__).resolve().parents[2]
EXPECTED = {
    "clustering": "network_clustering.png",
    "efficiency": "network_efficiency.png",
    "aspect": "imagery_aspect.png",
}


def test_build_tutorials_writes_phase0_names(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    pytest.importorskip("networkx")
    pytest.importorskip("rasterio")
    path = REPO / "scripts" / "build_tutorials.py"
    spec = importlib.util.spec_from_file_location("build_tutorials", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    written = module.main(tmp_path)
    for key, name in EXPECTED.items():
        assert key in written
        assert written[key].name == name
        assert_gallery_png(written[key])
    assert (tmp_path / "network_streets.png").is_file()
