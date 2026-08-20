"""Catalog and tutorial snippets must stay executable on toys / the fixture."""

from __future__ import annotations

from pathlib import Path

import pytest

import urbancode as uc

FIXTURE = Path(__file__).resolve().parents[2] / "examples" / "data" / "punggol_pocket"


def test_catalog_network_toys() -> None:
    nx = pytest.importorskip("networkx")
    graph = nx.Graph()
    graph.add_node(0, x=0.0, y=0.0)
    graph.add_node(1, x=1.0, y=0.0)
    graph.add_node(2, x=0.0, y=1.0)
    graph.add_edge(0, 1, length=10.0)
    graph.add_edge(1, 2, length=10.0)
    graph.add_edge(2, 0, length=10.0)
    between = uc.network.centrality(graph, metric="betweenness")
    reach = uc.network.accessibility(graph, radius=20, metric="reachability")
    clustered = uc.network.clustering(graph)
    efficient = uc.network.local_efficiency(graph)
    assert between.metadata["unit"] == "dimensionless"
    assert reach.metadata["unit"] == "count"
    assert clustered.data.nodes[0]["clustering"] == 1.0
    assert efficient.data.nodes[0]["local_efficiency"] == 1.0


def test_catalog_fixture_calls() -> None:
    pytest.importorskip("networkx")
    if not FIXTURE.is_dir():
        pytest.skip("punggol fixture missing")
    city = uc.load(FIXTURE)
    clustered = uc.network.clustering(city["streets"], radius=500)
    assert clustered.metadata["processing"]["definition"] == "watts_strogatz_local"
    assert clustered.metadata["column"] == "clustering"
