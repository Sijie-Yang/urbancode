from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from run_recipes import discover, run_one  # noqa: E402

OFFLINE_SKIP = {
    "streetview/comfort_punggol",
    "streetview/segmentation_punggol",
    "streetview/object_detection_punggol",
    "streetview/scene_recognition_punggol",
    "cli/streetview_comfort",
    "climate/utci_real",
}


def _recipe_id(path: Path) -> str:
    return path.relative_to(ROOT / "examples" / "recipes").with_suffix("").as_posix()


@pytest.mark.parametrize("path", discover(), ids=_recipe_id)
def test_offline_recipe(path: Path, tmp_path: Path) -> None:
    recipe_id = _recipe_id(path)
    if path.name.startswith("_"):
        pytest.skip("helper")
    if recipe_id.startswith("adapters/"):
        pytest.importorskip("osmnx") if "osmnx" in recipe_id else None
    if recipe_id in OFFLINE_SKIP and os.environ.get("UC_RUN_HEAVY_RECIPES") != "1":
        pytest.skip("heavy or live-adjacent recipe")
    if "network" in recipe_id or "fusion" in recipe_id or "units" in recipe_id or "core" in recipe_id:
        pytest.importorskip("geopandas")
        pytest.importorskip("networkx")
    if "imagery" in recipe_id or "fusion" in recipe_id:
        pytest.importorskip("rasterio")
        if recipe_id.startswith("imagery/") and recipe_id.split("/")[1] in {
            "read_punggol",
            "slope_punggol",
            "aspect_punggol",
            "hillshade_punggol",
        }:
            try:
                import rioxarray  # noqa: F401
            except Exception:
                pytest.skip("rioxarray is not importable in this environment")
    if "streetview" in recipe_id and "filename" not in recipe_id:
        pytest.importorskip("cv2")
    out = run_one(path, tmp_path)
    assert isinstance(out, dict)
    assert "figures" in out and "artifacts" in out and "summary" in out
    for figure in out["figures"]:
        assert Path(figure).is_file()
        assert Path(figure).stat().st_size > 100
