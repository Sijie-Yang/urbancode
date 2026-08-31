"""Named network metrics that return a plottable Layer."""

from __future__ import annotations

import heapq
import math
from typing import Any

from urbancode.city import Layer
from urbancode.errors import require_extra

_CENTRALITY = {"betweenness", "closeness"}
_ACCESS = {"reachability"}


def centrality(
    graph: Any,
    metric: str = "betweenness",
    radius: float | None = None,
    weight: str = "length",
) -> Layer:
    """Compute betweenness or closeness on graph nodes.

    Args:
        graph: NetworkX graph or graph :class:`~urbancode.city.Layer`.
        metric: ``"betweenness"`` or ``"closeness"``.
        radius: Optional shortest-path cutoff in the units of ``weight``;
            normally metres for OSM walk graphs.
        weight: Edge attribute used as distance. Geometry length is used when
            possible if the named attribute is missing.

    Returns:
        A new graph :class:`~urbancode.city.Layer`. Its nodes carry an
        attribute named after ``metric``; the input graph is not mutated.

    Raises:
        ValueError: If ``metric`` is not supported.
        TypeError: If ``graph`` is not a graph or graph Layer.

    Notes:
        Values describe the supplied graph extract. A clipped study area can
        strongly affect shortest paths, especially near its boundary.
    """
    if metric not in _CENTRALITY:
        raise ValueError(
            f"unknown centrality metric {metric!r}; use 'betweenness' or 'closeness'"
        )
    nx = require_extra("networkx", "network")
    source = graph
    G = _isolate_graph(_as_graph(graph, nx))
    used_weight = _ensure_weight(G, weight)
    if metric == "betweenness":
        values = _betweenness(G, radius, used_weight, nx)
        attr = "betweenness"
    else:
        values = _closeness(G, radius, used_weight, nx)
        attr = "closeness"
    nx.set_node_attributes(G, values, attr)
    parent = source.name if isinstance(source, Layer) else "streets"
    crs = source.crs if isinstance(source, Layer) else None
    return _stamp(Layer(
        name=metric,
        kind="graph",
        data=G,
        crs=crs,
        source="urbancode.network.centrality",
        metadata={
            "processing": {
                "op": "centrality",
                "metric": metric,
                "definition": (
                    "brandes_betweenness"
                    if metric == "betweenness"
                    else "closeness"
                ),
                "radius": radius,
                "weight": used_weight,
                "directed": False,
                "multigraph_reduction": "minimum_edge_weight",
                "normalization": "standard",
            },
            "column": attr,
            "unit": "dimensionless",
            "parent": parent,
        },
    ))


def accessibility(
    graph: Any,
    radius: float,
    metric: str = "reachability",
    weight: str = "length",
) -> Layer:
    """Count other nodes reachable within a network-distance cutoff.

    Args:
        graph: NetworkX graph or graph :class:`~urbancode.city.Layer`.
        radius: Non-negative path-length cutoff in the units of ``weight``;
            normally metres for OSM walk graphs.
        metric: Currently only ``"reachability"``.
        weight: Edge attribute used as path length.

    Returns:
        A new graph :class:`~urbancode.city.Layer` whose nodes carry the
        integer-like ``reachability`` attribute. The unit is a node count, not
        population, jobs, or travel time.

    Raises:
        ValueError: If ``radius`` is negative or ``metric`` is unsupported.
        TypeError: If ``graph`` is not a graph or graph Layer.
    """
    if metric not in _ACCESS:
        raise ValueError(f"unknown accessibility metric {metric!r}; use 'reachability'")
    if radius < 0:
        raise ValueError("radius must be non-negative")
    nx = require_extra("networkx", "network")
    source = graph
    G = _isolate_graph(_as_graph(graph, nx))
    used_weight = _ensure_weight(G, weight)
    values = _reachability(G, radius, used_weight, nx)
    nx.set_node_attributes(G, values, "reachability")
    parent = source.name if isinstance(source, Layer) else "streets"
    crs = source.crs if isinstance(source, Layer) else None
    return _stamp(Layer(
        name=metric,
        kind="graph",
        data=G,
        crs=crs,
        source="urbancode.network.accessibility",
        metadata={
            "processing": {
                "op": "accessibility",
                "metric": metric,
                "definition": "reachable_node_count",
                "radius": radius,
                "weight": used_weight,
                "directed": False,
                "multigraph_reduction": "minimum_edge_weight",
                "normalization": "none",
            },
            "column": "reachability",
            "unit": "count",
            "parent": parent,
        },
    ))


def clustering(
    graph: Any,
    radius: float | None = None,
    weight: str = "length",
) -> Layer:
    """Watts–Strogatz local clustering coefficient (experimental).

    Neighborhood is the 1-hop neighbors. For degree ``k >= 2``,
    ``C = 2 e / (k (k - 1))`` where ``e`` is the number of edges among
    those neighbors; otherwise ``C = 0``. If ``radius`` is set, a neighbor
    counts only when its incident edge ``weight`` is ``<= radius``.
    This is not a community detector. Street graphs are sparse, so many
    nodes are 0. Status: experimental.
    """
    if radius is not None and radius < 0:
        raise ValueError("radius must be non-negative")
    nx = require_extra("networkx", "network")
    source = graph
    raw = _as_graph(graph, nx)
    if len(raw) == 0:
        raise ValueError("clustering requires a graph with at least one node")
    G = _isolate_graph(raw)
    used_weight = _ensure_weight(G, weight)
    simple = _simple_undirected(G, used_weight, nx)
    values = _clustering_values(simple, radius, used_weight)
    nx.set_node_attributes(G, values, "clustering")
    parent = source.name if isinstance(source, Layer) else "streets"
    crs = source.crs if isinstance(source, Layer) else None
    return _stamp(Layer(
        name="clustering",
        kind="graph",
        data=G,
        crs=crs,
        source="urbancode.network.clustering",
        metadata={
            "processing": {
                "op": "clustering",
                "definition": "watts_strogatz_local",
                "radius": radius,
                "weight": used_weight,
                "directed": False,
                "multigraph_reduction": "minimum_edge_weight",
                "normalization": "none",
                "status": "experimental",
            },
            "column": "clustering",
            "unit": "dimensionless",
            "parent": parent,
        },
    ))


def local_efficiency(
    graph: Any,
    radius: float | None = None,
    weight: str = "length",
) -> Layer:
    """Latora–Marchiori node local efficiency (experimental).

    For each node ``i``, take 1-hop neighbors ``N_i`` (optionally filtered
    by incident edge ``weight <= radius``), drop ``i``, and average
    ``1 / hop_distance`` over neighbor pairs. Disconnected pairs contribute
    0. The value is dimensionless in ``[0, 1]``. Status: experimental.
    """
    if radius is not None and radius < 0:
        raise ValueError("radius must be non-negative")
    nx = require_extra("networkx", "network")
    source = graph
    raw = _as_graph(graph, nx)
    if len(raw) == 0:
        raise ValueError("local_efficiency requires a graph with at least one node")
    G = _isolate_graph(raw)
    used_weight = _ensure_weight(G, weight)
    simple = _simple_undirected(G, used_weight, nx)
    values = _local_efficiency_values(simple, radius, used_weight, nx)
    nx.set_node_attributes(G, values, "local_efficiency")
    parent = source.name if isinstance(source, Layer) else "streets"
    crs = source.crs if isinstance(source, Layer) else None
    return _stamp(Layer(
        name="local_efficiency",
        kind="graph",
        data=G,
        crs=crs,
        source="urbancode.network.local_efficiency",
        metadata={
            "processing": {
                "op": "local_efficiency",
                "definition": "latora_marchiori_node",
                "radius": radius,
                "weight": used_weight,
                "directed": False,
                "multigraph_reduction": "minimum_edge_weight",
                "normalization": "unweighted_hop",
                "status": "experimental",
            },
            "column": "local_efficiency",
            "unit": "dimensionless",
            "parent": parent,
        },
    ))


def _stamp(layer: Layer) -> Layer:
    from urbancode.provenance import stamp_layer

    stamp_layer(layer)
    return layer


def _isolate_graph(graph: Any) -> Any:
    """Copy structure and attribute dicts so the caller’s graph is untouched."""
    clone = graph.__class__()
    clone.graph.update(dict(graph.graph))
    for node, data in graph.nodes(data=True):
        clone.add_node(node, **dict(data))
    if graph.is_multigraph():
        for u, v, key, data in graph.edges(keys=True, data=True):
            clone.add_edge(u, v, key=key, **dict(data))
    else:
        for u, v, data in graph.edges(data=True):
            clone.add_edge(u, v, **dict(data))
    return clone


def _as_graph(source: Any, nx: Any) -> Any:
    if isinstance(source, Layer):
        if source.data is None:
            raise TypeError(f"layer {source.name!r} has no graph")
        source = source.data
    if hasattr(source, "nodes") and hasattr(source, "edges"):
        return source
    raise TypeError(
        f"expected a Layer or NetworkX graph; got {type(source).__name__}"
    )


def _ensure_weight(graph: Any, weight: str) -> str | None:
    has = False
    for _u, _v, data in graph.edges(data=True):
        if weight in data:
            try:
                data[weight] = float(data[weight])
                has = True
            except (TypeError, ValueError):
                pass
    if has:
        return weight
    geographic = _looks_lonlat(graph)
    for u, v, data in graph.edges(data=True):
        x0, y0 = _xy(graph, u)
        x1, y1 = _xy(graph, v)
        data[weight] = _haversine_m(y0, x0, y1, x1) if geographic else math.hypot(x1 - x0, y1 - y0)
    return weight


def _looks_lonlat(graph: Any) -> bool:
    xs, ys = [], []
    for node in list(graph.nodes)[:8]:
        try:
            x, y = _xy(graph, node)
        except ValueError:
            return False
        xs.append(x)
        ys.append(y)
    if not xs:
        return False
    return max(abs(v) for v in xs) <= 180 and max(abs(v) for v in ys) <= 90


def _xy(graph: Any, node: Any) -> tuple[float, float]:
    data = graph.nodes[node]
    if "x" not in data or "y" not in data:
        raise ValueError(
            f"graph node {node!r} is missing x/y coordinates; "
            "centrality needs an OSM-style graph or edge lengths"
        )
    return float(data["x"]), float(data["y"])


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _simple_undirected(graph: Any, weight: str | None, nx: Any) -> Any:
    simple = nx.Graph()
    simple.add_nodes_from(graph.nodes(data=True))
    for u, v, data in graph.edges(data=True):
        w = float(data.get(weight, 1.0)) if weight else 1.0
        if simple.has_edge(u, v):
            if weight:
                simple[u][v][weight] = min(simple[u][v].get(weight, w), w)
        else:
            payload = {weight: w} if weight else {}
            simple.add_edge(u, v, **payload)
    return simple


def _betweenness(graph: Any, radius: float | None, weight: str | None, nx: Any) -> dict[Any, float]:
    simple = _simple_undirected(graph, weight, nx)
    if radius is None:
        return nx.betweenness_centrality(simple, weight=weight, normalized=True)
    return _betweenness_cutoff(simple, float(radius), weight)


def _betweenness_cutoff(graph: Any, cutoff: float, weight: str | None) -> dict[Any, float]:
    betweenness = {node: 0.0 for node in graph}
    n = len(graph)
    for source in graph:
        stack: list[Any] = []
        parents = {node: [] for node in graph}
        sigma = dict.fromkeys(graph, 0.0)
        sigma[source] = 1.0
        dist = {source: 0.0}
        heap: list[tuple[float, int, Any]] = [(0.0, 0, source)]
        counter = 1
        seen = {source: 0.0}
        while heap:
            d_v, _i, v = heapq.heappop(heap)
            if v in dist and d_v > dist[v]:
                continue
            stack.append(v)
            for w, edata in graph[v].items():
                cost = float(edata.get(weight, 1.0)) if weight else 1.0
                nd = d_v + cost
                if nd > cutoff:
                    continue
                if w not in seen or nd < seen[w]:
                    seen[w] = nd
                    dist[w] = nd
                    sigma[w] = sigma[v]
                    parents[w] = [v]
                    heapq.heappush(heap, (nd, counter, w))
                    counter += 1
                elif abs(nd - seen[w]) <= 1e-12:
                    sigma[w] += sigma[v]
                    parents[w].append(v)
        delta = dict.fromkeys(graph, 0.0)
        while stack:
            w = stack.pop()
            for v in parents[w]:
                if sigma[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != source:
                betweenness[w] += delta[w]
    if n > 2:
        scale = 1.0 / ((n - 1) * (n - 2))
        for node in betweenness:
            betweenness[node] *= scale
    return betweenness


def _closeness(graph: Any, radius: float | None, weight: str | None, nx: Any) -> dict[Any, float]:
    simple = _simple_undirected(graph, weight, nx)
    if radius is None:
        return nx.closeness_centrality(simple, distance=weight)
    out: dict[Any, float] = {}
    for node in simple:
        distances = nx.single_source_dijkstra_path_length(
            simple, node, cutoff=radius, weight=weight
        )
        distances.pop(node, None)
        if distances:
            total = sum(distances.values())
            out[node] = len(distances) / total if total > 0 else 0.0
        else:
            out[node] = 0.0
    return out


def _incident_neighbors(graph: Any, node: Any, radius: float | None, weight: str | None) -> list[Any]:
    neighbors: list[Any] = []
    for nbr, edata in graph[node].items():
        cost = float(edata.get(weight, 1.0)) if weight else 1.0
        if radius is None or cost <= radius:
            neighbors.append(nbr)
    return neighbors


def _clustering_values(
    graph: Any, radius: float | None, weight: str | None
) -> dict[Any, float]:
    out: dict[Any, float] = {}
    for node in graph:
        neigh = _incident_neighbors(graph, node, radius, weight)
        degree = len(neigh)
        if degree < 2:
            out[node] = 0.0
            continue
        triangles = 0
        for i, u in enumerate(neigh):
            for v in neigh[i + 1 :]:
                if graph.has_edge(u, v):
                    triangles += 1
        out[node] = (2.0 * triangles) / (degree * (degree - 1))
    return out


def _local_efficiency_values(
    graph: Any, radius: float | None, weight: str | None, nx: Any
) -> dict[Any, float]:
    out: dict[Any, float] = {}
    for node in graph:
        neigh = _incident_neighbors(graph, node, radius, weight)
        degree = len(neigh)
        if degree < 2:
            out[node] = 0.0
            continue
        subgraph = graph.subgraph(neigh)
        total = 0.0
        for i, u in enumerate(neigh):
            for v in neigh[i + 1 :]:
                try:
                    dist = nx.shortest_path_length(subgraph, u, v)
                    if dist > 0:
                        total += 1.0 / dist
                except (nx.NetworkXNoPath, nx.NetworkXError):
                    pass
        out[node] = (2.0 * total) / (degree * (degree - 1))
    return out


def _reachability(graph: Any, radius: float, weight: str | None, nx: Any) -> dict[Any, float]:
    simple = _simple_undirected(graph, weight, nx)
    out: dict[Any, float] = {}
    for node in simple:
        distances = nx.single_source_dijkstra_path_length(
            simple, node, cutoff=radius, weight=weight
        )
        out[node] = float(len(distances) - (1 if node in distances else 0))
    return out
