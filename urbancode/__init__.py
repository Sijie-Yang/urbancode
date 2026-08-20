"""UrbanCode: multimodal urban analysis.

``import urbancode`` stays light: torch, osmnx, and rasterio are loaded only
when the corresponding submodule is accessed.
"""

from __future__ import annotations

import importlib
from typing import Any

from urbancode._version import __version__

__author__ = "Sijie Yang"
__description__ = "A package for universal urban analysis"

__all__ = [
    "AnalysisUnits",
    "City",
    "IndicatorRecord",
    "IndicatorResult",
    "Layer",
    "StudyArea",
    "adapters",
    "backends",
    "calculate_accessibility_metrics",
    "betweenness_centrality_radius",
    "climate",
    "closeness_centrality_radius",
    "clustering_coefficient_radius",
    "download_network",
    "fetch",
    "fusion",
    "graph_from_gdf",
    "graph_to_gdf",
    "images",
    "imagery",
    "indicators",
    "perception",
    "load",
    "load_saved_network",
    "local_efficiency_radius",
    "network",
    "reachability_radius",
    "save_network",
    "streetview",
    "svi",
    "units",
]

_NETWORK_ATTRS = {
    "network",
    "download_network",
    "save_network",
    "load_saved_network",
    "graph_to_gdf",
    "graph_from_gdf",
    "closeness_centrality_radius",
    "betweenness_centrality_radius",
    "reachability_radius",
    "local_efficiency_radius",
    "clustering_coefficient_radius",
    "calculate_accessibility_metrics",
}


def __getattr__(name: str) -> Any:
    """Lazy-import submodules and re-exported network helpers."""
    if name in {"City", "Layer", "load"}:
        city = importlib.import_module(".city", __name__)
        globals()["City"] = city.City
        globals()["Layer"] = city.Layer
        globals()["load"] = city.load
        return globals()[name]

    if name == "StudyArea":
        area = importlib.import_module(".area", __name__)
        globals()["StudyArea"] = area.StudyArea
        return area.StudyArea

    if name in {"AnalysisUnits", "units"}:
        units_mod = importlib.import_module(".units", __name__)
        globals()["units"] = units_mod
        globals()["AnalysisUnits"] = units_mod.AnalysisUnits
        return globals()[name]

    if name in {"IndicatorRecord", "IndicatorResult", "indicators"}:
        ind = importlib.import_module(".indicators", __name__)
        globals()["indicators"] = ind
        globals()["IndicatorRecord"] = ind.IndicatorRecord
        globals()["IndicatorResult"] = ind.IndicatorResult
        return globals()[name]

    if name == "fusion":
        fusion = importlib.import_module(".fusion", __name__)
        globals()["fusion"] = fusion
        return fusion

    if name == "backends":
        backends = importlib.import_module(".backends", __name__)
        globals()["backends"] = backends
        return backends

    if name == "climate":
        climate = importlib.import_module(".climate", __name__)
        globals()["climate"] = climate
        return climate

    if name == "streetview":
        streetview = importlib.import_module(".streetview", __name__)
        globals()["streetview"] = streetview
        return streetview

    if name == "fetch":
        fetch_mod = importlib.import_module(".fetch", __name__)
        globals()["fetch"] = fetch_mod.fetch
        return fetch_mod.fetch

    if name == "adapters":
        adapters = importlib.import_module(".adapters", __name__)
        globals()["adapters"] = adapters
        return adapters

    if name == "svi":
        svi = importlib.import_module(".svi", __name__)
        globals()["svi"] = svi
        return svi

    if name == "images":
        images = importlib.import_module(".images", __name__)
        globals()["images"] = images
        return images

    if name == "perception":
        perception = importlib.import_module(".perception", __name__)
        globals()["perception"] = perception
        return perception

    if name == "imagery":
        imagery = importlib.import_module(".imagery", __name__)
        globals()["imagery"] = imagery
        return imagery

    if name == "network":
        net = importlib.import_module(".network", __name__)
        globals()["network"] = net
        return net

    if name in _NETWORK_ATTRS:
        net = importlib.import_module(".network", __name__)
        globals()["network"] = net
        from urbancode.network.core import (
            download_network,
            graph_from_gdf,
            graph_to_gdf,
            load_saved_network,
            save_network,
        )
        from urbancode.network._radius import (
            betweenness_centrality_radius,
            calculate_accessibility_metrics,
            closeness_centrality_radius,
            clustering_coefficient_radius,
            local_efficiency_radius,
            reachability_radius,
        )

        exported = {
            "download_network": download_network,
            "save_network": save_network,
            "load_saved_network": load_saved_network,
            "graph_to_gdf": graph_to_gdf,
            "graph_from_gdf": graph_from_gdf,
            "closeness_centrality_radius": closeness_centrality_radius,
            "betweenness_centrality_radius": betweenness_centrality_radius,
            "reachability_radius": reachability_radius,
            "local_efficiency_radius": local_efficiency_radius,
            "clustering_coefficient_radius": clustering_coefficient_radius,
            "calculate_accessibility_metrics": calculate_accessibility_metrics,
        }
        globals().update(exported)
        if name == "network":
            return net
        if name in globals():
            return globals()[name]
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
