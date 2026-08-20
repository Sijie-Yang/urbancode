from urbancode.network.layers import (
    ALL_OSM_LAYERS,
    DEFAULT_OSM_LAYERS,
    OSM_LAYER_SPECS,
    normalize_layers,
)
import pytest


def test_default_is_not_all() -> None:
    assert normalize_layers(None) == ["streets"]
    assert "transit" not in DEFAULT_OSM_LAYERS
    assert "admin" not in DEFAULT_OSM_LAYERS
    assert set(DEFAULT_OSM_LAYERS) < set(ALL_OSM_LAYERS)


def test_all_is_explicit() -> None:
    assert normalize_layers("all") == list(ALL_OSM_LAYERS)


def test_unknown_layer() -> None:
    with pytest.raises(ValueError, match="unknown OSM layers"):
        normalize_layers(["moon"])


def test_thematic_views_and_geometry_filters() -> None:
    water_natural = OSM_LAYER_SPECS["water"]["tags"]["natural"]
    parks_natural = OSM_LAYER_SPECS["parks"]["tags"]["natural"]
    assert "water" in water_natural
    assert "wood" in parks_natural
    assert OSM_LAYER_SPECS["pois"]["geom_types"] == ["Point"]
    assert "Polygon" in OSM_LAYER_SPECS["parks"]["geom_types"]
    assert OSM_LAYER_SPECS["admin"]["default_admin_level"] == ("8", "9", "10")
    assert "leisure" not in OSM_LAYER_SPECS["landuse"]["tags"]


def test_cache_key_includes_admin_level() -> None:
    from urbancode.network.fetch import _cache_key

    a = _cache_key(
        "admin",
        "Tinyville",
        None,
        None,
        "walk",
        source="osm",
        admin_level=("8",),
    )
    b = _cache_key(
        "admin",
        "Tinyville",
        None,
        None,
        "walk",
        source="osm",
        admin_level=("9", "10"),
    )
    assert a != b
