"""Place-name geocoding that does not require the network extra."""

from __future__ import annotations

from typing import Any


def geocode_bbox(place: str) -> tuple[float, float, float, float]:
    """Return ``(west, south, east, north)`` for a place name.

    Uses Nominatim via geopy (``urbancode[imagery]``). osmnx is only a fallback
    if geopy is missing and the network extra is installed.
    """
    if not place or not str(place).strip():
        raise ValueError("place is required")
    try:
        return _geopy_bbox(place)
    except ImportError:
        pass
    try:
        return _osmnx_bbox(place)
    except ImportError as exc:
        raise ImportError(
            "Geocoding a place name requires geopy "
            '(pip install "urbancode[imagery]") or osmnx '
            '(pip install "urbancode[network]"). Pass bbox= to skip geocoding.'
        ) from exc


def _geopy_bbox(place: str) -> tuple[float, float, float, float]:
    from geopy.geocoders import Nominatim

    geolocator = Nominatim(user_agent="urbancode")
    location = geolocator.geocode(place, exactly_one=True)
    if location is None:
        raise ValueError(f"could not geocode {place!r}")
    raw: dict[str, Any] = getattr(location, "raw", {}) or {}
    box = raw.get("boundingbox")
    if box and len(box) == 4:
        south, north, west, east = (float(v) for v in box)
        return west, south, east, north
    lon = float(location.longitude)
    lat = float(location.latitude)
    pad = 0.01
    return lon - pad, lat - pad, lon + pad, lat + pad


def _osmnx_bbox(place: str) -> tuple[float, float, float, float]:
    import osmnx as ox

    gdf = ox.geocode_to_gdf(place)
    west, south, east, north = gdf.total_bounds
    return float(west), float(south), float(east), float(north)
