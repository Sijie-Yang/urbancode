from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from check_recipe_figures import catalog_figures, existing_static_figures  # noqa: E402


def test_existing_recipe_figures_are_nonblank() -> None:
    errors = existing_static_figures()
    assert errors == []


BLOCKED_PLACEHOLDER_PNGS = (
    "recipes/streetview/segmentation_punggol.png",
    "recipes/streetview/object_detection_punggol.png",
    "recipes/streetview/scene_recognition_punggol.png",
    "recipes/streetview/comfort_punggol.png",
)


def test_blocked_ml_placeholder_pngs_are_gone() -> None:
    from catalog_lib import FIGURES

    leftover = [name for name in BLOCKED_PLACEHOLDER_PNGS if (FIGURES / name).is_file()]
    assert leftover == []


def test_catalog_figures_when_required() -> None:
    require = os.environ.get("UC_REQUIRE_RECIPE_FIGURES") == "1"
    errors = catalog_figures(require=require)
    assert errors == []


PLACEHOLDER_MARKERS = (
    b"No hardcoded scores",
    b"Run urbancode[streetview]",
    b"placeholder",
)


def test_committed_pngs_contain_no_placeholder_text() -> None:
    from catalog_lib import FIGURES

    offenders = []
    for path in FIGURES.rglob("*.png"):
        data = path.read_bytes()
        for marker in PLACEHOLDER_MARKERS:
            if marker.lower() in data.lower():
                offenders.append(f"{path.relative_to(FIGURES)} contains {marker!r}")
    assert offenders == []


def test_offline_catalog_figures_are_substantial() -> None:
    from catalog_lib import figure_path, is_blocked, load_catalog

    thin = []
    for item in load_catalog():
        if is_blocked(item) or not item.get("offline") or not item.get("figure"):
            continue
        path = figure_path(item)
        if path is None or not path.is_file():
            thin.append(f"{item['id']}: missing {item.get('figure')}")
            continue
        if path.stat().st_size < 8_000:
            thin.append(f"{item['id']}: {path.name} is {path.stat().st_size} bytes")
    assert thin == []


def test_recipe_rst_is_not_a_default_stub() -> None:
    from catalog_lib import RECIPES_RST

    stubs = []
    for path in RECIPES_RST.rglob("*.rst"):
        text = path.read_text(encoding="utf-8")
        if "Defaults are those of" in text:
            stubs.append(str(path.relative_to(RECIPES_RST)))
    assert stubs == []
