"""Download OSM (or Overture) layers into a City."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from urbancode.cache import network_dir
from urbancode.city import City, handle_layer_error
from urbancode.errors import require_extra
from urbancode.network.layers import OSM_LAYER_SPECS, normalize_layers, spec_for
from urbancode.network.osmnx_api import features_from_bbox, graph_from_bbox


def fetch(
    place: str | None = None,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    polygon: Any = None,
    layers: str | Iterable[str] | None = None,
    network_type: str = "walk",
    source: str = "osm",
    on_error: str = "raise",
    refresh: bool = False,
    use_cache: bool = True,
    admin_level: Iterable[str] | None = None,
) -> City:
    """Fetch vector / street-graph layers for a place, bbox, or polygon.

    Args:
        place: Geocodable place name. Mutually exclusive with bbox/polygon
            unless used only as a label.
        bbox: ``(west, south, east, north)`` in WGS84.
        polygon: Shapely polygon in WGS84.
        layers: Layer names, a comma string, or ``"all"`` (explicit only).
            Default is ``["streets"]``.
        network_type: OSMnx network type for the ``streets`` layer.
        source: ``"osm"`` or ``"overture"``. No automatic merge.
        on_error: ``raise``, ``warn``, or ``ignore``.
        refresh: Ignore on-disk cache.
        use_cache: Write/read the UrbanCode network cache.
        admin_level: Values kept on the ``admin`` layer (default 8/9/10).

    Returns:
        A :class:`~urbancode.city.City` with requested layers.
    """
    if source == "overture":
        raise NotImplementedError(
            "Overture fetch is not implemented in v0.3. "
            "Pass source='osm', or install later extras. "
            "OSM and Overture are never auto-merged."
        )
    if source != "osm":
        raise ValueError("source must be 'osm' or 'overture'")

    ox = require_extra("osmnx", "network")
    require_extra("geopandas", "vector")

    names = normalize_layers(layers)
    levels = tuple(admin_level) if admin_level is not None else spec_for("admin").get(
        "default_admin_level", ("8", "9", "10")
    )
    city = City(
        place=place,
        metadata={
            "source": source,
            "network_type": network_type,
            "admin_level": list(levels),
        },
    )
    queried_at = datetime.now(timezone.utc).isoformat()

    boundary = _resolve_boundary(ox, place=place, bbox=bbox, polygon=polygon)
    if boundary is not None:
        city.boundary = boundary

    for name in names:
        try:
            layer_data, kind, crs, extra_meta = _load_layer(
                ox,
                name=name,
                place=place,
                bbox=bbox,
                polygon=polygon,
                network_type=network_type,
                refresh=refresh,
                use_cache=use_cache,
                admin_level=levels,
                source=source,
            )
            city.add_layer(
                name,
                layer_data,
                kind=kind,  # type: ignore[arg-type]
                crs=crs,
                source=source,
                metadata={
                    "queried_at": queried_at,
                    "network_type": network_type if name == "streets" else None,
                    "tags": spec_for(name).get("tags"),
                    **extra_meta,
                },
            )
        except Exception as exc:
            handle_layer_error(city, name, exc, on_error)
    return city


def _resolve_boundary(ox, *, place, bbox, polygon):
    gpd = require_extra("geopandas", "vector")
    if polygon is not None:
        return gpd.GeoDataFrame(geometry=[polygon], crs="EPSG:4326")
    if bbox is not None:
        west, south, east, north = bbox
        from shapely.geometry import box

        return gpd.GeoDataFrame(
            geometry=[box(west, south, east, north)], crs="EPSG:4326"
        )
    if place:
        try:
            gdf = ox.geocode_to_gdf(place)
            return gdf
        except Exception:
            return None
    return None


def _load_layer(
    ox,
    *,
    name: str,
    place: str | None,
    bbox: tuple[float, float, float, float] | None,
    polygon: Any,
    network_type: str,
    refresh: bool,
    use_cache: bool,
    admin_level: tuple[str, ...] | None = None,
    source: str = "osm",
) -> tuple[Any, str, Any, dict[str, Any]]:
    spec = spec_for(name)
    cache_path = _cache_path(
        name,
        place,
        bbox,
        polygon,
        network_type,
        source=source,
        admin_level=admin_level,
    )
    if use_cache and cache_path.exists() and not refresh:
        return _read_cached(cache_path, spec["kind"])

    if spec.get("network"):
        graph = _download_graph(ox, place, bbox, polygon, network_type)
        if use_cache:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            ox.save_graphml(graph, cache_path)
        return graph, "graph", "EPSG:4326", {"n_nodes": graph.number_of_nodes()}

    tags = spec["tags"]
    gdf = _download_features(ox, place, bbox, polygon, tags)
    gdf = _filter_layer_geometries(gdf, spec, admin_level=admin_level)
    if use_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        gdf.to_file(cache_path, driver="GPKG")
    geom_types = sorted({str(t) for t in gdf.geom_type}) if len(gdf) else []
    return gdf, "vector", getattr(gdf, "crs", "EPSG:4326"), {"geom_types": geom_types}


def _download_graph(ox, place, bbox, polygon, network_type):
    if polygon is not None:
        return ox.graph_from_polygon(polygon, network_type=network_type)
    if bbox is not None:
        west, south, east, north = bbox
        return graph_from_bbox(ox, west, south, east, north, network_type)
    if not place:
        raise ValueError("place, bbox, or polygon is required")
    return ox.graph_from_place(place, network_type=network_type)


def _download_features(ox, place, bbox, polygon, tags):
    if polygon is not None:
        return ox.features_from_polygon(polygon, tags)
    if bbox is not None:
        west, south, east, north = bbox
        return features_from_bbox(ox, west, south, east, north, tags)
    if not place:
        raise ValueError("place, bbox, or polygon is required")
    return ox.features_from_place(place, tags)


def _filter_layer_geometries(gdf, spec, admin_level=None):
    if gdf is None or len(gdf) == 0:
        return gdf
    allowed = spec.get("geom_types")
    if allowed:
        gdf = gdf[gdf.geom_type.isin(list(allowed))]
    if spec is OSM_LAYER_SPECS.get("admin") or "default_admin_level" in spec:
        levels = admin_level or spec.get("default_admin_level")
        if levels is not None and "admin_level" in gdf.columns:
            gdf = gdf[gdf["admin_level"].astype(str).isin(set(levels))]
    return gdf


CACHE_SCHEMA = 1
OSMNX_MAJOR = 2


def _cache_key(
    name,
    place,
    bbox,
    polygon,
    network_type,
    *,
    source: str = "osm",
    admin_level=None,
) -> str:
    payload = {
        "cache_schema": CACHE_SCHEMA,
        "source": source,
        "layer": name,
        "layer_spec": OSM_LAYER_SPECS[name],
        "admin_level": sorted(str(x) for x in (admin_level or ())),
        "network_type": network_type,
        "osmnx_major": OSMNX_MAJOR,
        "place": place,
        "bbox": list(bbox) if bbox else None,
        "polygon": str(polygon) if polygon is not None else None,
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


def _cache_path(
    name,
    place,
    bbox,
    polygon,
    network_type,
    *,
    source: str = "osm",
    admin_level=None,
) -> Path:
    digest = _cache_key(
        name,
        place,
        bbox,
        polygon,
        network_type,
        source=source,
        admin_level=admin_level,
    )
    suffix = ".graphml" if OSM_LAYER_SPECS[name].get("network") else ".gpkg"
    return network_dir() / f"{name}_{digest}{suffix}"


def _read_cached(path: Path, kind: str):
    if kind == "graph":
        ox = require_extra("osmnx", "network")
        graph = ox.load_graphml(path)
        return graph, "graph", "EPSG:4326", {"cached": True}
    gpd = require_extra("geopandas", "vector")
    gdf = gpd.read_file(path)
    return gdf, "vector", getattr(gdf, "crs", None), {"cached": True}


class _CallableModule(type(sys.modules[__name__])):
    """Keep ``uc.network.fetch(...)`` working after the submodule is imported."""

    def __call__(self, *args: Any, **kwargs: Any):
        return fetch(*args, **kwargs)


sys.modules[__name__].__class__ = _CallableModule
