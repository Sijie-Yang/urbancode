"""Live example scripts. Default pytest run skips these."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.live

REPO = Path(__file__).resolve().parents[2]


def _load(filename: str):
    path = REPO / "examples" / "live" / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_live_network_small_bbox(tmp_path: Path) -> None:
    pytest.importorskip("osmnx")
    result = _load("01_network_small_bbox.py").main(tmp_path)
    assert Path(result["city"]).is_dir()


def test_live_imagery_small_bbox(tmp_path: Path) -> None:
    pytest.importorskip("rasterio")
    pytest.importorskip("pystac_client")
    result = _load("02_imagery_small_bbox.py").main(tmp_path)
    assert Path(result["city"]).is_dir()
