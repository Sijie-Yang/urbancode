from __future__ import annotations

from unittest.mock import patch

import networkx as nx
import pytest

from urbancode.network.layers import normalize_layers


class _FakeOx:
    def geocode_to_gdf(self, place):
        gpd = pytest.importorskip("geopandas")
        from shapely.geometry import box

        return gpd.GeoDataFrame(geometry=[box(0, 0, 1, 1)], crs="EPSG:4326")

    def graph_from_place(self, place, network_type="walk"):
        graph = nx.MultiDiGraph()
        graph.add_node(1, x=0, y=0)
        graph.add_node(2, x=1, y=1)
        graph.add_edge(1, 2, 0, length=10)
        return graph

    def save_graphml(self, graph, path):
        nx.write_graphml(graph, path)

    def load_graphml(self, path):
        return nx.read_graphml(path)

    def features_from_place(self, place, tags):
        gpd = pytest.importorskip("geopandas")
        from shapely.geometry import Point

        return gpd.GeoDataFrame(
            {"amenity": ["cafe"], "geometry": [Point(0.1, 0.1)]},
            crs="EPSG:4326",
        )


def test_network_fetch_uses_mock_and_cache(cache_dir, tmp_path):
    pytest.importorskip("geopandas")
    import urbancode.network.fetch as network_fetch_mod

    fake = _FakeOx()

    def require(module, extra):
        if module == "osmnx":
            return fake
        return __import__(module)

    with patch.object(network_fetch_mod, "require_extra", require):
        city = network_fetch_mod.fetch(
            place="Tinyville",
            layers=["streets", "pois"],
            network_type="walk",
        )
    assert "streets" in city
    assert "pois" in city
    assert city.layer("streets").kind == "graph"
    assert city.layer("pois").source == "osm"
    assert city.layer("pois").metadata.get("tags")


def test_overture_not_implemented():
    from urbancode.network.fetch import fetch

    with pytest.raises(NotImplementedError, match="Overture"):
        fetch(place="X", source="overture")


def test_normalize_used_by_fetch_default():
    assert normalize_layers(None) == ["streets"]
