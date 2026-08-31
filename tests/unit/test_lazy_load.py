from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from urbancode.city import City, load

FIXTURE = Path(__file__).resolve().parents[2] / "examples" / "data" / "punggol_pocket"


def test_load_raster_only_does_not_need_geopandas(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom():
        raise AssertionError("geopandas should not be required")

    monkeypatch.setattr("urbancode.city._require_geopandas", boom)
    city = load(FIXTURE, layers=["dem"], lazy=True)
    assert list(city.keys()) == ["dem"]
    assert "buildings" not in city
    assert city.layers["dem"].data is None
    assert city.layers["dem"].path
    assert city.layers["dem"].lazy is True


def test_load_unknown_layer_raises() -> None:
    with pytest.raises(KeyError, match="unknown layer"):
        load(FIXTURE, layers=["not_a_layer"], lazy=True)


def test_describe_and_quality_do_not_materialize(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "urbancode.city._require_geopandas",
        lambda: (_ for _ in ()).throw(AssertionError("geopandas")),
    )
    city = load(FIXTURE, layers=["dem"], lazy=True)
    summary = city.describe()
    assert summary["layers"][0]["name"] == "dem"
    assert summary["layers"][0]["loaded"] is False
    report = city.quality_report()
    assert report["issues"] == []
    assert city.layers["dem"].data is None


def test_lazy_table_materializes(tmp_path: Path) -> None:
    city = City(place="T")
    city.add_layer("scores", pd.DataFrame({"v": [1, 2]}), kind="table")
    out = city.to_dir(tmp_path / "city")
    loaded = load(out, layers=["scores"], lazy=True)
    assert loaded.layers["scores"].data is None
    frame = loaded["scores"]
    assert list(frame["v"]) == [1, 2]
    assert loaded.layers["scores"].lazy is False


def test_lazy_save_copies_files_without_materialize(tmp_path: Path) -> None:
    city = City(place="T")
    city.add_layer("scores", pd.DataFrame({"v": [3, 4]}), kind="table")
    first = city.to_dir(tmp_path / "one")
    lazy = load(first, lazy=True)
    assert lazy.layers["scores"].data is None
    second = lazy.to_dir(tmp_path / "two")
    assert (second / "layers" / "scores.csv").exists() or (
        second / "layers" / "scores.parquet"
    ).exists()
    reloaded = load(second)
    assert list(reloaded["scores"]["v"]) == [3, 4]
