#!/usr/bin/env python3
"""Add water and parent-city locator context to real pockets.

Prefers OSM Overpass. If the network is unavailable, water is polygonized
from the committed Sentinel-2 NDWI and the locator is a documented
parent-city envelope (not a cadastral boundary).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_lib import REAL_DATA  # noqa: E402
from data.dataset_manifest import write_checksums  # noqa: E402

CITIES = {
    "punggol": {
        "locator_place": "Singapore",
        "locator_envelope": (103.60, 1.15, 104.10, 1.48),
        "locator_note": "Geographic envelope of Singapore for the inset. Not an OSM admin polygon.",
    },
    "kallio": {
        "locator_place": "Helsinki, Finland",
        "locator_envelope": (24.80, 60.13, 25.24, 60.30),
        "locator_note": "Geographic envelope of Helsinki for the inset. Not an OSM admin polygon.",
    },
    "greenwich_village": {
        "locator_place": "New York City, United States",
        "locator_envelope": (-74.26, 40.49, -73.70, 40.92),
        "locator_note": "Geographic envelope of New York City for the inset. Not an OSM admin polygon.",
    },
}


def _clip(gdf, bbox):
    import geopandas as gpd
    from shapely.geometry import box

    frame = gdf.to_crs("EPSG:4326") if gdf.crs is not None else gdf.set_crs("EPSG:4326")
    clipped = gpd.clip(frame, box(*bbox))
    return clipped[~clipped.geometry.is_empty].copy()


def _slim(gdf, columns: list[str]):
    keep = [c for c in columns if c in gdf.columns]
    return gdf[keep + ["geometry"]].copy() if keep else gdf[["geometry"]].copy()


def fetch_osm_features(bbox, tags: dict):
    import osmnx as ox

    from urbancode.network.osmnx_api import features_from_bbox

    ox.settings.timeout = 20
    ox.settings.overpass_rate_limit = False
    return features_from_bbox(ox, *bbox, tags)


def fetch_osm_locator(place: str):
    import osmnx as ox

    frame = ox.geocode_to_gdf(place)
    if frame.empty:
        raise RuntimeError(f"no locator geometry for {place!r}")
    metric = frame.estimate_utm_crs()
    simplified = frame.to_crs(metric).simplify(400, preserve_topology=True).to_crs("EPSG:4326")
    out = frame[["geometry"]].copy()
    out["geometry"] = simplified
    out["name"] = place
    out["source"] = "osmnx.geocode_to_gdf"
    return out


def water_from_ndwi(root: Path):
    import geopandas as gpd
    import numpy as np
    from rasterio.features import shapes
    from shapely.geometry import shape

    import urbancode as uc

    city = uc.load(root, layers=["sentinel2"], lazy=False)
    ndwi = uc.imagery.ndwi(city.layers["sentinel2"])
    from urbancode.imagery.source import open_raster

    src = open_raster(ndwi)
    mask = np.isfinite(src.array_2d) & (src.array_2d >= 0.15)
    geoms = []
    for geom, value in shapes(mask.astype("uint8"), mask=mask, transform=src.transform):
        if int(value) != 1:
            continue
        geoms.append(shape(geom))
    if not geoms:
        return gpd.GeoDataFrame(geometry=[], crs=src.crs)
    frame = gpd.GeoDataFrame({"source": ["sentinel2-ndwi"] * len(geoms)}, geometry=geoms, crs=src.crs)
    return frame.to_crs("EPSG:4326")


def envelope_locator(spec: dict):
    import geopandas as gpd
    from shapely.geometry import box

    west, south, east, north = spec["locator_envelope"]
    return gpd.GeoDataFrame(
        {
            "name": [spec["locator_place"]],
            "source": ["documented_parent_city_envelope"],
            "note": [spec["locator_note"]],
        },
        geometry=[box(west, south, east, north)],
        crs="EPSG:4326",
    )


def patch_manifest(root: Path, extra_layers: list[dict], locator_rel: str, water_source: str, locator_source: str) -> None:
    manifest_path = root / "manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    existing = {item.get("name") for item in data.get("layers") or []}
    layers = list(data.get("layers") or [])
    for item in extra_layers:
        if item["name"] not in existing:
            layers.append(item)
        else:
            layers = [item if old.get("name") == item["name"] else old for old in layers]
    data["layers"] = layers
    meta = data.setdefault("metadata", {})
    meta["locator"] = locator_rel
    data["locator"] = locator_rel
    data["context"] = {
        "water_source": water_source,
        "locator_source": locator_source,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "scripts/data/build_context_layers.py",
    }
    steps = list(data.get("processing_steps") or [])
    note = f"context layers: water from {water_source}; locator from {locator_source}"
    if note not in steps:
        steps.append(note)
    data["processing_steps"] = steps
    license_block = data.setdefault("license", {})
    license_block.setdefault("osm", "ODbL-1.0")
    license_block.setdefault("sentinel2", "Copernicus Sentinel license")
    attr = data.setdefault("attribution", {})
    attr.setdefault("osm", "© OpenStreetMap contributors (ODbL 1.0)")
    attr.setdefault("sentinel2", "Copernicus Sentinel-2 L2A via Microsoft Planetary Computer")
    manifest_path.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")


def build_city(name: str, *, offline: bool = False) -> Path:
    spec = CITIES[name]
    root = REAL_DATA / name
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    bbox = tuple(manifest.get("bbox") or manifest["metadata"]["bbox"])
    print(f"context {name} bbox={bbox}")
    water_source = "osm"
    locator_source = "osmnx.geocode_to_gdf"
    landuse = None
    try:
        if offline:
            raise RuntimeError("offline mode")
        water = _slim(
            _clip(
                fetch_osm_features(
                    bbox, {"natural": ["water", "bay"], "waterway": True, "water": True}
                ),
                bbox,
            ),
            ["name", "natural", "waterway", "water"],
        )
        landuse = _slim(_clip(fetch_osm_features(bbox, {"landuse": True}), bbox), ["name", "landuse"])
        locator = fetch_osm_locator(spec["locator_place"])
    except Exception as exc:
        print(f"OSM unavailable ({exc.__class__.__name__}); using Sentinel-2 NDWI + documented envelope")
        water = water_from_ndwi(root)
        locator = envelope_locator(spec)
        water_source = "sentinel2-ndwi>=0.15"
        locator_source = "documented_parent_city_envelope"
    layers_dir = root / "layers"
    context_dir = root / "context"
    layers_dir.mkdir(exist_ok=True)
    context_dir.mkdir(exist_ok=True)
    water_path = layers_dir / "water.gpkg"
    locator_path = context_dir / "locator_boundary.gpkg"
    water.to_file(water_path, driver="GPKG")
    locator.to_file(locator_path, driver="GPKG")
    extra = [
        {
            "name": "water",
            "kind": "vector",
            "path": "layers/water.gpkg",
            "crs": "EPSG:4326",
            "source": water_source,
            "metadata": {},
        }
    ]
    if landuse is not None and len(landuse):
        landuse_path = layers_dir / "landuse.gpkg"
        landuse.to_file(landuse_path, driver="GPKG")
        extra.append(
            {
                "name": "landuse",
                "kind": "vector",
                "path": "layers/landuse.gpkg",
                "crs": "EPSG:4326",
                "source": "osm",
                "metadata": {},
            }
        )
    patch_manifest(root, extra, "context/locator_boundary.gpkg", water_source, locator_source)
    files = [path for path in root.rglob("*") if path.is_file() and path.name != "checksums.sha256"]
    write_checksums(root, files)
    print(f"wrote {name}: water={len(water)} locator={locator_source}")
    return root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", choices=sorted(CITIES))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--offline", action="store_true", help="skip Overpass; use NDWI + envelopes")
    args = parser.parse_args()
    names = list(CITIES) if args.all else [args.city] if args.city else []
    if not names:
        parser.error("pass --city or --all")
    for name in names:
        build_city(name, offline=args.offline)
    return 0


if __name__ == "__main__":
    sys.exit(main())
