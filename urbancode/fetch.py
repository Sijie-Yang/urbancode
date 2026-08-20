"""Top-level multi-modal fetch. Modalities only expand presets."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from urbancode.city import City
from urbancode.network.layers import DEFAULT_OSM_LAYERS

MODALITY_PRESETS: dict[str, tuple[str, ...]] = {
    "osm": DEFAULT_OSM_LAYERS,
    "satellite": ("sentinel2",),
    "terrain": ("dem",),
}

NETWORK_LAYERS = set(DEFAULT_OSM_LAYERS) | {
    "streets",
    "buildings",
    "pois",
    "landuse",
    "water",
    "parks",
    "transit",
    "admin",
}
IMAGERY_LAYERS = {
    "sentinel2",
    "dem",
    "ndvi",
    "ndwi",
    "ndbi",
    "slope",
    "aspect",
    "hillshade",
}


def expand_modalities(modalities: Iterable[str] | None) -> list[str]:
    """Expand modality presets to layer names. Does not fetch."""
    if not modalities:
        return []
    names: list[str] = []
    for modality in modalities:
        key = modality.strip().lower()
        if key not in MODALITY_PRESETS:
            raise ValueError(
                f"unknown modality {modality!r}; known: {list(MODALITY_PRESETS)}"
            )
        for layer in MODALITY_PRESETS[key]:
            if layer not in names:
                names.append(layer)
    return names


NETWORK_OPTION_KEYS = frozenset(
    {"network_type", "admin_level", "source", "use_cache", "bbox"}
)
IMAGERY_OPTION_KEYS = frozenset(
    {"time", "cloud", "composite", "max_pixels", "bbox"}
)


def _validate_options(
    label: str, options: Mapping[str, Any] | None, allowed: frozenset[str]
) -> dict[str, Any]:
    if not options:
        return {}
    unknown = set(options) - allowed
    if unknown:
        raise ValueError(
            f"unknown {label} keys {sorted(unknown)}; allowed: {sorted(allowed)}"
        )
    return dict(options)


def fetch(
    place: str,
    modalities: Iterable[str] | None = None,
    layers: Iterable[str] | None = None,
    out: str | Path | None = None,
    on_error: str = "raise",
    refresh: bool = False,
    network_type: str = "walk",
    network_options: Mapping[str, Any] | None = None,
    imagery_options: Mapping[str, Any] | None = None,
) -> City:
    """Fetch selected layers for ``place`` into one :class:`City`.

    ``modalities`` only expands presets (``osm``, ``satellite``, ``terrain``).
    Precise requests should pass ``layers``. Failed layers are recorded on
    ``city.errors`` when ``on_error`` is ``warn`` or ``ignore``.

    Extra backend knobs go in ``network_options`` / ``imagery_options``.
    Unknown keys raise ``ValueError``.
    """
    net_opts = _validate_options("network_options", network_options, NETWORK_OPTION_KEYS)
    img_opts = _validate_options("imagery_options", imagery_options, IMAGERY_OPTION_KEYS)
    requested: list[str] = []
    for name in expand_modalities(modalities):
        if name not in requested:
            requested.append(name)
    if layers is not None:
        extra = list(layers) if not isinstance(layers, str) else [
            p.strip() for p in layers.split(",") if p.strip()
        ]
        for name in extra:
            if name not in requested:
                requested.append(name)
    if not requested:
        requested = ["streets"]

    unknown = [
        name
        for name in requested
        if name not in NETWORK_LAYERS and name not in IMAGERY_LAYERS
    ]
    if unknown:
        raise ValueError(f"unknown layers {unknown}")

    net_layers = [n for n in requested if n in NETWORK_LAYERS]
    img_layers = [n for n in requested if n in IMAGERY_LAYERS]

    city = City(place=place, metadata={"modalities": list(modalities or [])})

    if net_layers:
        from urbancode.network.fetch import fetch as network_fetch

        net_city = network_fetch(
            place=place,
            layers=net_layers,
            network_type=net_opts.get("network_type", network_type),
            on_error=on_error,
            refresh=refresh,
            bbox=net_opts.get("bbox"),
            source=net_opts.get("source", "osm"),
            use_cache=net_opts.get("use_cache", True),
            admin_level=net_opts.get("admin_level"),
        )
        _merge(city, net_city)

    if img_layers:
        from urbancode.imagery.fetch import fetch as imagery_fetch

        img_city = imagery_fetch(
            place=place,
            layers=img_layers,
            on_error=on_error,
            refresh=refresh,
            bbox=img_opts.get("bbox"),
            time=img_opts.get("time"),
            cloud=img_opts.get("cloud", 20),
            composite=img_opts.get("composite", "single"),
            max_pixels=img_opts.get("max_pixels", 25_000_000),
        )
        _merge(city, img_city)

    if out is not None:
        city.to_dir(out)
    return city


def _merge(target: City, source: City) -> None:
    if target.boundary is None and source.boundary is not None:
        target.boundary = source.boundary
    target.metadata.update(source.metadata)
    target.errors.extend(source.errors)
    for name, layer in source.layers.items():
        target.add_layer(
            name,
            layer.data,
            kind=layer.kind,
            path=layer.path,
            crs=layer.crs,
            source=layer.source,
            metadata=layer.metadata,
            overwrite=True,
        )
