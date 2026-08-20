from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_lib import (  # noqa: E402
    RECIPES_PY,
    analysis_items,
    is_blocked,
    load_catalog,
    recipe_py,
    validate_item,
)


def test_catalog_schema() -> None:
    errors: list[str] = []
    for item in load_catalog():
        errors.extend(validate_item(item))
    assert errors == []


def test_adapter_only_has_interop_file() -> None:
    missing: list[str] = []
    for item in load_catalog():
        if item["status"] != "adapter-only":
            continue
        path = RECIPES_PY / f"{item['interop']}.py"
        if not path.is_file():
            missing.append(str(path.relative_to(ROOT)))
    assert missing == []


def test_unblocked_recipe_paths_are_declared() -> None:
    for item in analysis_items():
        if is_blocked(item):
            assert item.get("recipe") in {None, ""}
            continue
        assert item.get("recipe")
        assert item.get("figure")
        assert item.get("dataset")
        assert recipe_py(item) is not None
