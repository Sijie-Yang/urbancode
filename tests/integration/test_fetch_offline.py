from __future__ import annotations

import importlib
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from urbancode.city import City
from urbancode.fetch import expand_modalities, fetch

_NETWORK_FETCH = importlib.import_module("urbancode.network.fetch")
_IMAGERY_FETCH = importlib.import_module("urbancode.imagery.fetch")


def test_modalities_expand_presets_only() -> None:
    assert expand_modalities(["satellite"]) == ["sentinel2"]
    assert expand_modalities(["terrain"]) == ["dem"]
    osm = expand_modalities(["osm"])
    assert osm == [
        "streets",
        "buildings",
        "pois",
        "landuse",
        "water",
        "parks",
    ]
    assert "transit" not in osm
    with pytest.raises(ValueError, match="unknown modality"):
        expand_modalities(["lidar"])


def test_fetch_partial_success_and_roundtrip(tmp_path: Path, cache_dir: Path) -> None:
    def fake_network(**kwargs):
        city = City(place=kwargs["place"])
        city.add_layer(
            "streets",
            pd.DataFrame({"id": [1]}),
            kind="table",
            source="osm",
        )
        return city

    def fake_imagery(**kwargs):
        city = City(place=kwargs.get("place"))
        city.record_error("sentinel2", "stac unavailable")
        return city

    with patch.object(_NETWORK_FETCH, "fetch", fake_network), patch.object(
        _IMAGERY_FETCH, "fetch", fake_imagery
    ):
        city = fetch(
            "Tinyville",
            modalities=["osm", "satellite"],
            out=tmp_path / "city",
            on_error="warn",
        )

    assert "streets" in city
    assert city.errors
    assert (tmp_path / "city" / "manifest.json").exists()
    loaded = City.from_dir(tmp_path / "city")
    assert loaded.place == "Tinyville"
    assert "streets" in loaded
    assert loaded.errors


def test_unknown_fetch_options_rejected() -> None:
    with pytest.raises(ValueError, match="unknown network_options"):
        fetch("X", layers=["streets"], network_options={"typo": 1})
    with pytest.raises(ValueError, match="unknown imagery_options"):
        fetch("X", layers=["ndvi"], imagery_options={"cloudd": 5})


def test_fetch_forwards_options(tmp_path: Path) -> None:
    seen: dict = {}

    def fake_network(**kwargs):
        seen["net"] = kwargs
        city = City(place=kwargs["place"])
        city.add_layer("streets", pd.DataFrame({"id": [1]}), kind="table")
        return city

    def fake_imagery(**kwargs):
        seen["img"] = kwargs
        city = City(place=kwargs.get("place"))
        city.add_layer("ndvi", pd.DataFrame({"v": [1]}), kind="table")
        return city

    with patch.object(_NETWORK_FETCH, "fetch", fake_network), patch.object(
        _IMAGERY_FETCH, "fetch", fake_imagery
    ):
        fetch(
            "Tinyville",
            layers=["streets", "ndvi"],
            network_options={"admin_level": ["8"], "source": "osm"},
            imagery_options={"cloud": 10, "time": "2025-01-01/2025-12-31"},
        )
    assert seen["net"]["admin_level"] == ["8"]
    assert seen["img"]["cloud"] == 10
    assert seen["img"]["time"] == "2025-01-01/2025-12-31"


def test_fetch_on_error_raise() -> None:
    def boom(**kwargs):
        raise RuntimeError("overpass down")

    with patch.object(_NETWORK_FETCH, "fetch", boom):
        with pytest.raises(RuntimeError, match="overpass down"):
            fetch("Tinyville", layers=["streets"], on_error="raise")
