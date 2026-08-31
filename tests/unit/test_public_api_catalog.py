"""Reverse coverage: public __all__ names must appear in the catalog."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_lib import load_catalog  # noqa: E402

PKG = ROOT / "urbancode"

SKIP_MODULES = {
    "adapters",
    "backends",
    "climate",
    "fusion",
    "images",
    "imagery",
    "indicators",
    "network",
    "perception",
    "streetview",
    "svi",
    "units",
}
SKIP_CONSTANTS = {
    "ALL_OSM_LAYERS",
    "DEFAULT_OSM_LAYERS",
    "OSM_LAYER_SPECS",
}
TOP_LEVEL_ALIASES = {
    "download_network": "uc.network.download_network",
    "save_network": "uc.network.save_network",
    "load_saved_network": "uc.network.load_saved_network",
    "graph_to_gdf": "uc.network.graph_to_gdf",
    "graph_from_gdf": "uc.network.graph_from_gdf",
    "closeness_centrality_radius": "uc.network.closeness_centrality_radius",
    "betweenness_centrality_radius": "uc.network.betweenness_centrality_radius",
    "reachability_radius": "uc.network.reachability_radius",
    "local_efficiency_radius": "uc.network.local_efficiency_radius",
    "clustering_coefficient_radius": "uc.network.clustering_coefficient_radius",
    "calculate_accessibility_metrics": "uc.network.calculate_accessibility_metrics",
    "fetch": "uc.fetch",
    "load": "uc.load",
    "StudyArea": "uc.StudyArea.from_bbox",
    "City": "uc.load",
    "Layer": "uc.load",
    "AnalysisUnits": "uc.units.grid",
    "IndicatorRecord": "uc.IndicatorResult.save",
    "IndicatorResult": "uc.IndicatorResult.save",
}
CLASS_METHODS = (
    "uc.IndicatorResult.save",
    "uc.IndicatorResult.load",
    "uc.IndicatorResult.plot",
    "uc.IndicatorResult.to_layer",
)


def _all_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                return [elt.value for elt in node.value.elts if isinstance(elt, ast.Constant)]
    return []


def _catalog_functions() -> set[str]:
    return {item["function"] for item in load_catalog()}


def test_submodule_all_is_catalogued() -> None:
    catalog = _catalog_functions()
    missing = []
    mapping = {
        PKG / "network" / "__init__.py": "uc.network",
        PKG / "imagery" / "__init__.py": "uc.imagery",
        PKG / "climate" / "__init__.py": "uc.climate",
        PKG / "streetview" / "__init__.py": "uc.svi",
        PKG / "svi" / "__init__.py": "uc.svi",
        PKG / "images.py": "uc.images",
        PKG / "perception" / "__init__.py": "uc.perception",
    }
    for path, prefix in mapping.items():
        for name in _all_names(path):
            if name in SKIP_CONSTANTS:
                continue
            key = f"{prefix}.{name}"
            if key not in catalog:
                missing.append(key)
    for name in ("grid", "hexgrid", "from_layer"):
        if f"uc.units.{name}" not in catalog:
            missing.append(f"uc.units.{name}")
    for name in ("aggregate", "combine", "aggregate_many"):
        if f"uc.fusion.{name}" not in catalog:
            missing.append(f"uc.fusion.{name}")
    assert missing == [], f"public names missing from capabilities.yaml: {missing}"


def test_toplevel_all_is_classified() -> None:
    catalog = _catalog_functions()
    missing = []
    for name in _all_names(PKG / "__init__.py"):
        if name in SKIP_MODULES or name == "svi":
            continue
        if name in TOP_LEVEL_ALIASES:
            if TOP_LEVEL_ALIASES[name] not in catalog:
                missing.append(f"uc.{name} -> {TOP_LEVEL_ALIASES[name]}")
            continue
        if f"uc.{name}" not in catalog:
            missing.append(f"uc.{name}")
    assert missing == [], missing


def test_indicator_methods_are_catalogued() -> None:
    catalog = _catalog_functions()
    missing = [name for name in CLASS_METHODS if name not in catalog]
    assert missing == []


def test_svi_is_the_catalogued_namespace() -> None:
    assert "svi" in _all_names(PKG / "__init__.py")
    assert all(not item["function"].startswith("uc.streetview") for item in load_catalog())
    assert any(item["function"].startswith("uc.svi.") for item in load_catalog())


def test_blocked_items_have_no_fake_offline_figure() -> None:
    for item in load_catalog():
        if not item.get("blocked"):
            continue
        assert item.get("recipe") in {None, ""}
        assert item.get("figure") in {None, ""}
        assert item.get("offline") is False
