"""Street network and OSM vector layers."""

from __future__ import annotations

from typing import Any

from .layers import ALL_OSM_LAYERS, DEFAULT_OSM_LAYERS, OSM_LAYER_SPECS

__all__ = [
    "ALL_OSM_LAYERS",
    "DEFAULT_OSM_LAYERS",
    "OSM_LAYER_SPECS",
    "accessibility",
    "betweenness_centrality_radius",
    "calculate_accessibility_metrics",
    "centrality",
    "closeness_centrality_radius",
    "clustering",
    "clustering_coefficient_radius",
    "download_network",
    "fetch",
    "graph_from_gdf",
    "graph_to_gdf",
    "load_saved_network",
    "local_efficiency",
    "local_efficiency_radius",
    "reachability_radius",
    "save_network",
]


def __getattr__(name: str) -> Any:
    if name == "fetch":
        # Load fetch.py via `.fetch`, not `from . import fetch` (that recurses
        # through this __getattr__). Caching the function makes
        # `import urbancode.network.fetch` return the callable, same as
        # `uc.network.fetch`. The submodule stays in sys.modules for
        # `from urbancode.network.fetch import fetch`.
        from .fetch import fetch as fetch_fn

        globals()["fetch"] = fetch_fn
        return fetch_fn
    if name in {"centrality", "accessibility", "clustering", "local_efficiency"}:
        from urbancode.errors import require_extra

        require_extra("networkx", "network")
        from .metrics import accessibility, centrality, clustering, local_efficiency

        globals()["centrality"] = centrality
        globals()["accessibility"] = accessibility
        globals()["clustering"] = clustering
        globals()["local_efficiency"] = local_efficiency
        return globals()[name]
    if name in {
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
    }:
        from urbancode.errors import require_extra

        require_extra("osmnx", "network")
        require_extra("geopandas", "vector")
        from ._radius import (
            betweenness_centrality_radius,
            calculate_accessibility_metrics,
            closeness_centrality_radius,
            clustering_coefficient_radius,
            local_efficiency_radius,
            reachability_radius,
        )
        from .core import (
            download_network,
            graph_from_gdf,
            graph_to_gdf,
            load_saved_network,
            save_network,
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
        return exported[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
