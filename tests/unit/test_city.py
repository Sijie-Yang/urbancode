from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from urbancode.city import City, Layer


def test_getitem_returns_data_layer_returns_metadata() -> None:
    city = City(place="Testville")
    frame = pd.DataFrame({"a": [1, 2]})
    city.add_layer("scores", frame, kind="table", source="unit")
    assert list(city.keys()) == ["scores"]
    assert city["scores"] is frame
    layer = city.layer("scores")
    assert isinstance(layer, Layer)
    assert layer.source == "unit"
    assert layer.kind == "table"


def test_duplicate_layer_requires_overwrite() -> None:
    city = City()
    city.add_layer("streets", [1], kind="table")
    with pytest.raises(ValueError, match="already exists"):
        city.add_layer("streets", [2], kind="table")
    city.add_layer("streets", [2], kind="table", overwrite=True)
    assert city["streets"] == [2]


def test_to_dir_from_dir_roundtrip(tmp_path: Path) -> None:
    city = City(place="Testville", metadata={"note": "roundtrip"})
    city.add_layer(
        "scores",
        pd.DataFrame({"value": [1.5, 2.5]}),
        kind="table",
        source="unit",
        metadata={"unit": "score"},
    )
    city.record_error("sentinel2", "offline")
    out = city.to_dir(tmp_path / "city")
    assert (out / "manifest.json").exists()
    loaded = City.from_dir(out)
    assert loaded.place == "Testville"
    assert loaded.metadata["note"] == "roundtrip"
    assert len(loaded.errors) == 1
    assert list(loaded["scores"]["value"]) == [1.5, 2.5]
    assert loaded.layer("scores").source == "unit"
