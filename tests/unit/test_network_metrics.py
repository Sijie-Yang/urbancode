from __future__ import annotations

import copy

import pytest

import urbancode as uc
from urbancode.city import Layer


def _xy_graph(nx, nodes, edges, *, directed=False, multi=False):
    graph = nx.MultiDiGraph() if multi else (nx.DiGraph() if directed else nx.Graph())
    for node, x, y in nodes:
        graph.add_node(node, x=x, y=y)
    for edge in edges:
        u, v, length = edge[0], edge[1], edge[2]
        graph.add_edge(u, v, length=length)
    return graph


def _values(layer: Layer, column: str) -> dict:
    return {node: layer.data.nodes[node][column] for node in layer.data.nodes}


def test_clustering_toy_graphs() -> None:
    nx = pytest.importorskip("networkx")
    triangle = _xy_graph(
        nx,
        [(0, 0, 0), (1, 1, 0), (2, 0, 1)],
        [(0, 1, 10.0), (1, 2, 10.0), (2, 0, 10.0)],
    )
    values = _values(uc.network.clustering(triangle), "clustering")
    assert values == {0: 1.0, 1: 1.0, 2: 1.0}

    path = _xy_graph(
        nx,
        [(0, 0, 0), (1, 1, 0), (2, 2, 0)],
        [(0, 1, 10.0), (1, 2, 10.0)],
    )
    values = _values(uc.network.clustering(path), "clustering")
    assert values == {0: 0.0, 1: 0.0, 2: 0.0}

    star = _xy_graph(
        nx,
        [(0, 0, 0), (1, 1, 0), (2, 0, 1), (3, -1, 0)],
        [(0, 1, 10.0), (0, 2, 10.0), (0, 3, 10.0)],
    )
    values = _values(uc.network.clustering(star), "clustering")
    assert values[0] == 0.0
    assert values[1] == 0.0

    cycle = nx.cycle_graph(5)
    for i, node in enumerate(cycle.nodes):
        cycle.nodes[node]["x"] = float(i)
        cycle.nodes[node]["y"] = 0.0
        for _, _, data in cycle.edges(node, data=True):
            data["length"] = 10.0
    values = _values(uc.network.clustering(cycle), "clustering")
    assert all(value == 0.0 for value in values.values())

    pair = _xy_graph(nx, [(0, 0, 0), (1, 1, 0)], [(0, 1, 10.0)])
    pair.add_node(2, x=5.0, y=5.0)
    values = _values(uc.network.clustering(pair), "clustering")
    assert values == {0: 0.0, 1: 0.0, 2: 0.0}


def test_clustering_radius_and_multigraph() -> None:
    nx = pytest.importorskip("networkx")
    triangle = _xy_graph(
        nx,
        [(0, 0, 0), (1, 1, 0), (2, 0, 1)],
        [(0, 1, 10.0), (1, 2, 10.0), (2, 0, 100.0)],
    )
    assert _values(uc.network.clustering(triangle, radius=9), "clustering") == {
        0: 0.0,
        1: 0.0,
        2: 0.0,
    }
    mid = _values(uc.network.clustering(triangle, radius=10), "clustering")
    assert mid[0] == 0.0
    assert mid[1] == 1.0
    assert mid[2] == 0.0
    wide = _values(uc.network.clustering(triangle, radius=100), "clustering")
    assert wide == {0: 1.0, 1: 1.0, 2: 1.0}

    multi = _xy_graph(
        nx,
        [(0, 0, 0), (1, 1, 0), (2, 0, 1)],
        [(0, 1, 100.0), (1, 2, 10.0), (2, 0, 10.0)],
        directed=True,
        multi=True,
    )
    multi.add_edge(0, 1, length=10.0)
    values = _values(uc.network.clustering(multi, radius=10), "clustering")
    assert values[0] == 1.0


def test_clustering_missing_length_and_empty() -> None:
    nx = pytest.importorskip("networkx")
    graph = nx.Graph()
    graph.add_node(0, x=0.0, y=0.0)
    graph.add_node(1, x=3.0, y=0.0)
    graph.add_node(2, x=0.0, y=4.0)
    graph.add_edge(0, 1)
    graph.add_edge(1, 2)
    graph.add_edge(2, 0)
    values = _values(uc.network.clustering(graph), "clustering")
    assert values == {0: 1.0, 1: 1.0, 2: 1.0}

    with pytest.raises(ValueError, match="at least one node"):
        uc.network.clustering(nx.Graph())
    zeros = _values(uc.network.clustering(graph, radius=0), "clustering")
    assert zeros == {0: 0.0, 1: 0.0, 2: 0.0}


def test_local_efficiency_toy_graphs() -> None:
    nx = pytest.importorskip("networkx")
    triangle = _xy_graph(
        nx,
        [(0, 0, 0), (1, 1, 0), (2, 0, 1)],
        [(0, 1, 10.0), (1, 2, 10.0), (2, 0, 10.0)],
    )
    values = _values(uc.network.local_efficiency(triangle), "local_efficiency")
    assert values == {0: 1.0, 1: 1.0, 2: 1.0}

    path = _xy_graph(
        nx,
        [(0, 0, 0), (1, 1, 0), (2, 2, 0)],
        [(0, 1, 10.0), (1, 2, 10.0)],
    )
    values = _values(uc.network.local_efficiency(path), "local_efficiency")
    assert values[0] == 0.0
    assert values[2] == 0.0
    assert values[1] == 0.0

    star = _xy_graph(
        nx,
        [(0, 0, 0), (1, 1, 0), (2, 0, 1), (3, -1, 0)],
        [(0, 1, 10.0), (0, 2, 10.0), (0, 3, 10.0)],
    )
    values = _values(uc.network.local_efficiency(star), "local_efficiency")
    assert values[0] == 0.0


def test_metrics_do_not_mutate_input() -> None:
    nx = pytest.importorskip("networkx")
    graph = _xy_graph(
        nx,
        [(0, 0, 0), (1, 1, 0), (2, 0, 1)],
        [(0, 1, 10.0), (1, 2, 10.0), (2, 0, 10.0)],
    )
    before = copy.deepcopy(nx.node_link_data(graph))
    clustered = uc.network.clustering(graph)
    efficient = uc.network.local_efficiency(graph)
    uc.network.centrality(graph, metric="betweenness")
    uc.network.accessibility(graph, radius=20, metric="reachability")
    assert nx.node_link_data(graph) == before
    assert "clustering" not in graph.nodes[0]
    assert "local_efficiency" not in graph.nodes[0]
    assert clustered.data is not graph
    assert efficient.data is not graph


def test_metric_metadata_contract() -> None:
    nx = pytest.importorskip("networkx")
    graph = _xy_graph(
        nx,
        [(0, 0, 0), (1, 1, 0), (2, 0, 1)],
        [(0, 1, 10.0), (1, 2, 10.0), (2, 0, 10.0)],
    )
    clustered = uc.network.clustering(graph, radius=500)
    proc = clustered.metadata["processing"]
    assert proc["op"] == "clustering"
    assert proc["definition"] == "watts_strogatz_local"
    assert proc["radius"] == 500
    assert proc["weight"] == "length"
    assert proc["directed"] is False
    assert proc["multigraph_reduction"] == "minimum_edge_weight"
    assert proc["normalization"] == "none"
    assert clustered.metadata["column"] == "clustering"
    assert clustered.metadata["unit"] == "dimensionless"
    assert clustered.metadata["parent"] == "streets"

    efficient = uc.network.local_efficiency(graph, radius=500)
    proc = efficient.metadata["processing"]
    assert proc["op"] == "local_efficiency"
    assert proc["definition"] == "latora_marchiori_node"
    assert proc["normalization"] == "unweighted_hop"
    assert efficient.metadata["unit"] == "dimensionless"

    between = uc.network.centrality(graph, metric="betweenness", radius=50)
    assert between.metadata["processing"]["definition"] == "brandes_betweenness"
    assert between.metadata["unit"] == "dimensionless"
    access = uc.network.accessibility(graph, radius=50)
    assert access.metadata["processing"]["definition"] == "reachable_node_count"
    assert access.metadata["unit"] == "count"


def test_fetch_stays_callable_after_submodule_import() -> None:
    pytest.importorskip("osmnx")
    assert callable(uc.network.fetch)
    assert uc.network.fetch.__name__ == "fetch"
    import urbancode.network.fetch as fetch_mod

    assert fetch_mod.__name__ == "fetch"
    assert uc.network.fetch is fetch_mod
    from urbancode.network.fetch import fetch as fetch_fn

    assert fetch_fn is uc.network.fetch


def test_accessibility_stays_callable_after_legacy_helpers() -> None:
    pytest.importorskip("networkx")
    import inspect

    assert inspect.isfunction(uc.network.accessibility)
    assert callable(uc.network.reachability_radius)
    assert inspect.isfunction(uc.network.accessibility)
    assert uc.network.accessibility.__module__ == "urbancode.network.metrics"
