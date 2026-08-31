"""Shared capability-catalog helpers for scripts and tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "docs" / "source" / "catalog" / "capabilities.yaml"
RECIPES_PY = ROOT / "examples" / "recipes"
RECIPES_RST = ROOT / "docs" / "source" / "reference" / "recipes"
FIGURES = ROOT / "docs" / "source" / "_static"
REAL_DATA = ROOT / "examples" / "data" / "real"
CONTRACTS = ROOT / "examples" / "data" / "contracts"

STATUSES = {"stable", "experimental", "adapter-only", "planned", "compatibility", "legacy"}
REQUIRED_ALWAYS = ("id", "function", "status", "extra", "backend")
REQUIRED_ANALYSIS = (
    "domain",
    "urban_question",
    "input",
    "output",
    "unit",
    "offline",
    "limitations",
)
REQUIRED_WHEN_UNBLOCKED = ("dataset", "recipe", "figure", "workflow")
REAL_MANIFEST_FIELDS = (
    "dataset_id",
    "city_id",
    "place",
    "bbox",
    "physical_extent",
    "geographic_crs",
    "metric_crs",
    "source",
    "source_uri",
    "license",
    "attribution",
    "acquired_at",
    "temporal_extent",
    "original_item_id",
    "processing_steps",
    "file_checksums",
    "generated_by",
)


def load_catalog() -> list[dict[str, Any]]:
    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    return list(data["capabilities"])


def analysis_items(catalog: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    items = catalog if catalog is not None else load_catalog()
    return [item for item in items if item["status"] in {"stable", "experimental"}]


def is_blocked(item: dict[str, Any]) -> bool:
    return bool(item.get("blocked"))


def recipe_py(item: dict[str, Any]) -> Path | None:
    recipe = item.get("recipe")
    if not recipe:
        return None
    return RECIPES_PY / f"{recipe}.py"


def recipe_rst(item: dict[str, Any]) -> Path | None:
    recipe = item.get("recipe")
    if not recipe:
        return None
    return RECIPES_RST / f"{recipe}.rst"


def figure_path(item: dict[str, Any]) -> Path | None:
    figure = item.get("figure")
    if not figure:
        return None
    return FIGURES / figure


def dataset_dir(item: dict[str, Any]) -> Path | None:
    dataset = item.get("dataset")
    if not dataset:
        return None
    if dataset.startswith("contracts/"):
        return ROOT / "examples" / "data" / dataset
    return REAL_DATA / dataset


def validate_item(item: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_ALWAYS:
        if key not in item:
            errors.append(f"{item.get('id', '?')}: missing {key}")
    status = item.get("status")
    if status not in STATUSES:
        errors.append(f"{item.get('id', '?')}: bad status {status!r}")
    if str(item.get("function", "")).startswith("uc.streetview"):
        errors.append(f"{item.get('id', '?')}: catalog must list uc.svi, not uc.streetview")
    if status == "adapter-only":
        if not item.get("interop"):
            errors.append(f"{item.get('id')}: adapter-only needs interop")
        return errors
    if status in {"planned", "compatibility", "legacy"}:
        if status in {"compatibility", "legacy"} and not item.get("migration"):
            errors.append(f"{item.get('id')}: {status} needs migration")
        return errors
    if status in {"stable", "experimental"}:
        for key in REQUIRED_ANALYSIS:
            if key not in item:
                errors.append(f"{item.get('id')}: missing {key}")
        if not item.get("limitations"):
            errors.append(f"{item.get('id')}: limitations must be a non-empty list")
        if is_blocked(item):
            if item.get("recipe") not in {None, ""}:
                errors.append(f"{item.get('id')}: blocked item must set recipe: null")
            return errors
        for key in REQUIRED_WHEN_UNBLOCKED:
            if not item.get(key):
                errors.append(f"{item.get('id')}: missing {key}")
    return errors
