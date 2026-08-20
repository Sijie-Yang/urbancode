from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from urbancode.city import SCHEMA_VERSION, City, _safe_city_path, validate_layer_name
from urbancode.errors import CityIntegrityError


def test_unsafe_layer_name() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        validate_layer_name("../etc")
    city = City()
    with pytest.raises(ValueError, match="unsafe"):
        city.add_layer("..hidden", [1], kind="table")


def test_overwrite_false_rejects_existing_manifest(tmp_path: Path) -> None:
    city = City(place="A")
    city.add_layer("scores", pd.DataFrame({"v": [1]}), kind="table")
    out = city.to_dir(tmp_path / "city")
    other = City(place="B")
    other.add_layer("scores", pd.DataFrame({"v": [2]}), kind="table")
    with pytest.raises(FileExistsError):
        other.to_dir(out, overwrite=False)
    other.to_dir(out, overwrite=True)
    loaded = City.from_dir(out)
    assert loaded.place == "B"
    assert list(loaded["scores"]["v"]) == [2]
    manifest = (out / "manifest.json").read_text(encoding="utf-8")
    assert f'"schema_version": {SCHEMA_VERSION}' in manifest
    assert "urbancode_version" in manifest


def test_graph_writes_graphml_not_pickle(tmp_path: Path) -> None:
    nx = pytest.importorskip("networkx")
    graph = nx.Graph()
    graph.add_edge("a", "b")
    city = City(place="G")
    city.add_layer("streets", graph, kind="graph")
    out = city.to_dir(tmp_path / "city")
    assert (out / "layers" / "streets.graphml").exists()
    assert not list(out.rglob("*.pkl"))
    assert not list(out.rglob("*.pickle"))
    loaded = City.from_dir(out)
    assert loaded.layer("streets").kind == "graph"
    assert loaded["streets"].number_of_edges() == 1


def test_safe_city_path_rejects_escape(tmp_path: Path) -> None:
    root = tmp_path / "city"
    root.mkdir()
    with pytest.raises(CityIntegrityError, match="escapes"):
        _safe_city_path(root, "../victim.txt")
    with pytest.raises(CityIntegrityError, match="absolute"):
        _safe_city_path(root, str(tmp_path / "victim.txt"))
    with pytest.raises(CityIntegrityError, match="empty"):
        _safe_city_path(root, "")
    inside = _safe_city_path(root, "layers/foo.csv")
    assert inside == (root / "layers" / "foo.csv").resolve()


def test_malicious_manifest_cannot_read_or_delete_outside(tmp_path: Path) -> None:
    victim = tmp_path / "victim.txt"
    victim.write_text("secret", encoding="utf-8")
    city_dir = tmp_path / "city"
    city_dir.mkdir()
    (city_dir / "layers").mkdir()
    (city_dir / "layers" / "scores.csv").write_text("v\n1\n", encoding="utf-8")
    (city_dir / "manifest.json").write_text(
        """
        {
          "schema_version": 1,
          "place": "evil",
          "layers": [
            {"name": "leak", "kind": "table", "path": "../victim.txt"}
          ]
        }
        """,
        encoding="utf-8",
    )
    with pytest.raises(CityIntegrityError, match="escapes"):
        City.from_dir(city_dir)

    other = City(place="ok")
    other.add_layer("scores", pd.DataFrame({"v": [9]}), kind="table")
    other.to_dir(city_dir, overwrite=True)
    assert victim.read_text(encoding="utf-8") == "secret"
    assert victim.exists()


def test_graphml_uses_osmnx_when_available(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    from types import SimpleNamespace

    nx = pytest.importorskip("networkx")
    from urbancode import city as city_mod

    saved: dict[str, bool] = {}

    def save_graphml(graph, dest):
        saved["ok"] = True
        Path(dest).write_text("<graphml></graphml>", encoding="utf-8")

    def load_graphml(path):
        graph = nx.MultiDiGraph()
        graph.add_edge(1, 2, 0)
        return graph

    monkeypatch.setitem(
        sys.modules,
        "osmnx",
        SimpleNamespace(save_graphml=save_graphml, load_graphml=load_graphml),
    )
    graph = nx.MultiDiGraph()
    graph.add_edge(1, 2, 0, osmid=[10, 11], geometry="LINESTRING (0 0, 1 1)")
    dest = tmp_path / "streets.graphml"
    city_mod._write_graphml(graph, dest)
    assert saved.get("ok") is True
    loaded = city_mod._read_graphml(dest)
    assert loaded.number_of_edges() == 1


def test_from_dir_verify_checksum_and_schema(tmp_path: Path) -> None:
    city = City(place="A")
    city.add_layer("scores", pd.DataFrame({"v": [1]}), kind="table")
    out = city.to_dir(tmp_path / "city")
    loaded = City.from_dir(out, verify=True)
    assert list(loaded["scores"]["v"]) == [1]

    manifest_path = out / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["schema_version"] = 99
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CityIntegrityError, match="schema_version"):
        City.from_dir(out, verify=True)
