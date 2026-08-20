"""Central OSM layer registry. Layers are thematic views and may overlap."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

# Thematic views, not a mutually exclusive partition of OSM tags.
# pois keeps Point amenities; parks keeps park/wood polygons. leisure=park
# can appear in both if geometry types match each layer's filter.
OSM_LAYER_SPECS: dict[str, dict[str, Any]] = {
    "streets": {
        "kind": "graph",
        "description": "Street network via osmnx graph_from_*",
        "network": True,
    },
    "buildings": {
        "kind": "vector",
        "tags": {"building": True},
        "description": "Building footprints",
    },
    "pois": {
        "kind": "vector",
        "tags": {
            "amenity": True,
            "shop": True,
            "tourism": True,
            "leisure": ["cafe", "bar", "restaurant", "marketplace"],
        },
        "geom_types": ["Point"],
        "description": "POI points (amenity/shop/tourism). Parks polygons are a separate layer.",
    },
    "landuse": {
        "kind": "vector",
        "tags": {"landuse": True},
        "description": "OSM landuse polygons (leisure/natural live on other layers)",
    },
    "water": {
        "kind": "vector",
        "tags": {
            "natural": ["water", "bay", "strait", "coastline"],
            "waterway": True,
            "water": True,
        },
        "description": "Water bodies and waterways; natural=water lives here",
    },
    "parks": {
        "kind": "vector",
        "tags": {
            "leisure": ["park", "garden", "nature_reserve", "playground"],
            "natural": ["wood", "scrub", "grassland", "heath"],
        },
        "geom_types": ["Polygon", "MultiPolygon"],
        "description": "Park and woodland polygons; may overlap POI points thematically",
    },
    "transit": {
        "kind": "vector",
        "tags": {
            "public_transport": True,
            "highway": "bus_stop",
            "railway": True,
            "station": True,
        },
        "description": "Transit stops, stations, and railway ways",
    },
    "admin": {
        "kind": "vector",
        "tags": {"boundary": "administrative"},
        "description": "Administrative boundaries; filter with admin_level",
        "default_admin_level": ("8", "9", "10"),
    },
}

ALL_OSM_LAYERS = tuple(OSM_LAYER_SPECS)
DEFAULT_OSM_LAYERS = ("streets", "buildings", "pois", "landuse", "water", "parks")


def normalize_layers(layers: str | Iterable[str] | None) -> list[str]:
    """Expand ``'all'`` or validate an explicit layer list.

    ``layers='all'`` is opt-in only. Callers must not use it as a silent default
    for large cities.
    """
    if layers is None:
        return ["streets"]
    if isinstance(layers, str):
        if layers == "all":
            return list(ALL_OSM_LAYERS)
        layers = [part.strip() for part in layers.split(",") if part.strip()]
    names = list(layers)
    unknown = [name for name in names if name not in OSM_LAYER_SPECS]
    if unknown:
        raise ValueError(
            f"unknown OSM layers {unknown}; known: {list(OSM_LAYER_SPECS)}"
        )
    return names


def spec_for(name: str) -> Mapping[str, Any]:
    if name not in OSM_LAYER_SPECS:
        raise KeyError(name)
    return OSM_LAYER_SPECS[name]
