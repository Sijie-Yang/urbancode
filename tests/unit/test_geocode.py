from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest

from urbancode.geocode import geocode_bbox


def test_geopy_bbox_without_osmnx() -> None:
    fake = SimpleNamespace(
        longitude=103.8,
        latitude=1.3,
        raw={"boundingbox": ["1.2", "1.4", "103.7", "103.9"]},
    )

    class _Nom:
        def __init__(self, user_agent: str) -> None:
            assert user_agent == "urbancode"

        def geocode(self, place: str, exactly_one: bool = True):
            return fake

    geopy_mod = sys.modules.get("geopy") or ModuleType("geopy")
    geolocators = sys.modules.get("geopy.geocoders") or ModuleType("geopy.geocoders")
    geolocators.Nominatim = _Nom
    sys.modules["geopy"] = geopy_mod
    sys.modules["geopy.geocoders"] = geolocators

    had_osmnx = "osmnx" in sys.modules
    west, south, east, north = geocode_bbox("Somewhere")
    assert (west, south, east, north) == (103.7, 1.2, 103.9, 1.4)
    if not had_osmnx:
        assert "osmnx" not in sys.modules


def test_geocode_requires_place() -> None:
    with pytest.raises(ValueError):
        geocode_bbox("")
