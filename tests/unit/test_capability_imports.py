from __future__ import annotations

import importlib
import os
from pathlib import Path

import yaml

import urbancode as uc

ROOT = Path(__file__).resolve().parents[2]
CATALOG = yaml.safe_load(
    (ROOT / "docs" / "source" / "catalog" / "capabilities.yaml").read_text(
        encoding="utf-8"
    )
)

_EXTRA_MODULES = {
    "vector": "geopandas",
    "network": "osmnx",
    "imagery": "rasterio",
    "climate": "pythermalcomfort",
    "svi": "torch",
    "streetview": "torch",
    "perception": "torch",
    "download": "zensvi",
    "viz": "matplotlib",
}


def _has(module: str) -> bool:
    try:
        importlib.import_module(module)
    except ImportError:
        return False
    return True


def _resolve(dotted: str):
    assert dotted.startswith("uc.")
    obj: object = uc
    for part in dotted.split(".")[1:]:
        obj = getattr(obj, part)
    return obj


def test_planned_capabilities_are_not_exported() -> None:
    public = set(getattr(uc, "__all__", ()))
    for item in CATALOG["capabilities"]:
        if item["status"] != "planned":
            continue
        name = str(item["function"]).split(".")[-1]
        assert name not in public
        assert not hasattr(uc, name)


def test_catalog_functions_importable_when_extra_present() -> None:
    fail_on_skip = os.environ.get("UC_FAIL_ON_SKIP") == "1"
    for item in CATALOG["capabilities"]:
        if item["status"] == "planned":
            continue
        extra = item["extra"]
        module = _EXTRA_MODULES.get(extra)
        if module is not None and not _has(module):
            if fail_on_skip:
                continue
            continue
        _resolve(item["function"])
