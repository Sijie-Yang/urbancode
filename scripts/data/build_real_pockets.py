#!/usr/bin/env python3
"""Build comparable 2 km real city pockets. Never falls back to synthetic."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_lib import REAL_DATA  # noqa: E402
from data.dataset_manifest import write_checksums  # noqa: E402

TIME_WINDOW = "2024-06-01/2024-08-31"
NETWORK_TYPE = "walk"
WIDTH_M = 2000.0
HEIGHT_M = 2000.0
USER_AGENT = "UrbanCodeRealPockets/0.3 (https://github.com/Sijie-Yang/urbancode)"

CITIES = {
    "punggol": {
        "city_id": "punggol",
        "place": "Punggol, Singapore",
        "center": (103.910, 1.405),
        "season_note": (
            "Equatorial. The June-August window is a shared calendar "
            "window, not a shared growing season."
        ),
    },
    "kallio": {
        "city_id": "kallio",
        "place": "Kallio, Helsinki",
        "center": (24.950, 60.188),
        "season_note": "Northern-summer window (June-August 2024).",
    },
    "greenwich_village": {
        "city_id": "greenwich_village",
        "place": "Greenwich Village, New York",
        "center": (-73.999, 40.733),
        "season_note": "Northern-summer window (June-August 2024).",
    },
}


def metric_bbox(lon: float, lat: float) -> tuple[tuple[float, float, float, float], str]:
    from pyproj import Transformer

    from urbancode.area import utm_crs_from_lonlat

    crs = utm_crs_from_lonlat(lon, lat)
    to_m = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    to_ll = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    x, y = to_m.transform(lon, lat)
    west, south = to_ll.transform(x - WIDTH_M / 2.0, y - HEIGHT_M / 2.0)
    east, north = to_ll.transform(x + WIDTH_M / 2.0, y + HEIGHT_M / 2.0)
    return (west, south, east, north), crs


def _clip(gdf, bbox):
    import geopandas as gpd
    from shapely.geometry import box

    frame = gdf.to_crs("EPSG:4326") if gdf.crs is not None else gdf.set_crs("EPSG:4326")
    clipped = gpd.clip(frame, box(*bbox))
    return clipped[~clipped.geometry.is_empty].copy()


def _slim(gdf, columns: list[str]):
    keep = [c for c in columns if c in gdf.columns]
    return gdf[keep + ["geometry"]].copy() if keep else gdf[["geometry"]].copy()


def fetch_osm(place: str, bbox: tuple[float, float, float, float]):
    import osmnx as ox

    from urbancode.network.fetch import fetch as network_fetch

    ox.settings.timeout = 300
    ox.settings.overpass_rate_limit = True
    city = network_fetch(
        place=place,
        bbox=bbox,
        layers=["streets", "buildings", "parks", "pois", "water", "landuse"],
        network_type=NETWORK_TYPE,
        use_cache=True,
    )
    if city.errors:
        raise RuntimeError(f"OSM fetch errors for {place}: {city.errors}")
    buildings = _slim(_clip(city["buildings"], bbox), ["name", "building"])
    parks = _slim(_clip(city["parks"], bbox), ["name", "leisure", "natural"])
    pois = _slim(_clip(city["pois"], bbox), ["name", "amenity", "shop", "tourism"])
    water = _slim(
        _clip(city["water"], bbox) if "water" in city.layers else city["buildings"].iloc[0:0],
        ["name", "natural", "waterway", "water"],
    )
    landuse = _slim(
        _clip(city["landuse"], bbox) if "landuse" in city.layers else city["buildings"].iloc[0:0],
        ["name", "landuse"],
    )
    if buildings.empty:
        raise RuntimeError(f"{place}: buildings layer is empty after clip")
    return city["streets"], buildings, parks, pois, water, landuse


def fetch_rasters(bbox: tuple[float, float, float, float], tmp: Path) -> tuple[Path, Path, dict]:
    from urbancode.imagery.grid import reproject_to_reference, stack_to_reference
    from urbancode.imagery.stac import (
        DEM_COLLECTION,
        SENTINEL2_COLLECTION,
        SENTINEL_ASSETS,
        download_assets_windowed,
        search_items,
    )

    items = search_items(SENTINEL2_COLLECTION, bbox, datetime=TIME_WINDOW, cloud=40)
    if not items:
        raise RuntimeError(f"no Sentinel-2 items for {bbox} in {TIME_WINDOW}")
    optical = download_assets_windowed(
        items[:1],
        list(SENTINEL_ASSETS),
        tmp / "sentinel",
        bbox,
        max_pixels=4_000_000,
    )
    missing = [name for name in SENTINEL_ASSETS if name not in optical]
    if missing:
        raise RuntimeError(f"Sentinel-2 missing bands {missing}")
    stacked = stack_to_reference(
        {name: optical[name] for name in SENTINEL_ASSETS},
        tmp / "sentinel2.tif",
        reference="B08",
    )
    dem_items = search_items(DEM_COLLECTION, bbox, datetime=None, cloud=None)
    dem_assets = download_assets_windowed(
        dem_items[:1],
        ["data"],
        tmp / "dem",
        bbox,
        max_pixels=4_000_000,
    )
    dem = reproject_to_reference(
        next(iter(dem_assets.values())),
        tmp / "dem.tif",
        reference_path=stacked,
        resampling="bilinear",
    )
    item = items[0]
    meta = {
        "sentinel_item_ids": [item.id],
        "sentinel_datetime": item.properties.get("datetime"),
        "sentinel_cloud_cover": item.properties.get("eo:cloud_cover"),
        "sentinel_collection": SENTINEL2_COLLECTION,
        "dem_item_ids": [it.id for it in dem_items[:1]],
        "time": TIME_WINDOW,
        "bands": list(SENTINEL_ASSETS),
    }
    return stacked, dem, meta


def write_sidecar(out: Path, spec: dict, bbox, metric_crs: str, raster_meta: dict) -> None:
    generated = datetime.now(timezone.utc).isoformat()
    attribution = {
        "osm": "© OpenStreetMap contributors (ODbL 1.0)",
        "sentinel2": "Copernicus Sentinel-2 L2A via Microsoft Planetary Computer",
        "dem": "Copernicus DEM GLO-30 via Microsoft Planetary Computer",
    }
    manifest = {
        "dataset_id": f"{spec['city_id']}_real_v1",
        "city_id": spec["city_id"],
        "place": spec["place"],
        "bbox": list(bbox),
        "physical_extent": {"width": WIDTH_M, "height": HEIGHT_M, "unit": "metre"},
        "geographic_crs": "EPSG:4326",
        "metric_crs": metric_crs,
        "source": "osm+sentinel-2-l2a+cop-dem-glo-30",
        "source_uri": {
            "osm": "https://www.openstreetmap.org",
            "stac": "https://planetarycomputer.microsoft.com/api/stac/v1",
        },
        "license": {
            "osm": "ODbL-1.0",
            "sentinel2": "Copernicus Sentinel license",
            "dem": "Copernicus DEM license",
        },
        "attribution": attribution,
        "acquired_at": raster_meta.get("sentinel_datetime"),
        "temporal_extent": TIME_WINDOW,
        "original_item_id": {
            "sentinel2": raster_meta.get("sentinel_item_ids"),
            "dem": raster_meta.get("dem_item_ids"),
        },
        "processing_steps": [
            "2 km x 2 km box in local UTM",
            "OSM walk network and vector layers clipped to bbox",
            "Sentinel-2 L2A windowed read of B02,B03,B04,B08,B11",
            "Copernicus DEM GLO-30 resampled to the Sentinel grid",
        ],
        "file_checksums": {},
        "generated_by": "scripts/data/build_real_pockets.py",
        "generated_at": generated,
        "synthetic": False,
        "season_note": spec["season_note"],
        "network_type": NETWORK_TYPE,
        "raster": raster_meta,
    }
    city_manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    city_manifest["metadata"] = {
        **(city_manifest.get("metadata") or {}),
        **manifest,
        "bbox": list(bbox),
        "fixture": False,
    }
    (out / "manifest.json").write_text(
        json.dumps(city_manifest, indent=2, default=str) + "\n", encoding="utf-8"
    )
    (out / "dataset.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # dataset_manifest.py reads manifest.json at the dataset root.
    # Merge required real-dataset fields onto the City manifest.
    merged = {**city_manifest, **manifest}
    (out / "manifest.json").write_text(
        json.dumps(merged, indent=2, default=str) + "\n", encoding="utf-8"
    )
    (out / "LICENSE.md").write_text(
        f"# {spec['place']}\n\n"
        "Real 2 km x 2 km extract for UrbanCode docs. Not a city-wide dump.\n\n"
        "## OpenStreetMap\n\n"
        "© OpenStreetMap contributors. ODbL 1.0.\n"
        "https://www.openstreetmap.org/copyright\n\n"
        "## Sentinel-2\n\n"
        "Copernicus Sentinel-2 L2A via Microsoft Planetary Computer.\n\n"
        "## DEM\n\n"
        "Copernicus DEM GLO-30 via Microsoft Planetary Computer.\n",
        encoding="utf-8",
    )
    (out / "README.md").write_text(
        f"# {spec['place']}\n\n"
        f"Physical extent: {WIDTH_M:.0f} m x {HEIGHT_M:.0f} m in {metric_crs}.\n"
        f"Calendar window: {TIME_WINDOW}. {spec['season_note']}\n"
        f"Sentinel-2 item: {raster_meta.get('sentinel_item_ids')}\n"
        f"Cloud cover: {raster_meta.get('sentinel_cloud_cover')}\n",
        encoding="utf-8",
    )
    files = [
        path
        for path in out.rglob("*")
        if path.is_file() and path.name not in {"checksums.sha256"}
    ]
    write_checksums(out, files)


def build_city(name: str, *, overwrite: bool = False) -> Path:
    spec = CITIES[name]
    out = REAL_DATA / name
    if out.exists() and not overwrite:
        if (out / "manifest.json").exists():
            print(f"exists {out} (pass --overwrite to rebuild)")
            return out
    bbox, metric_crs = metric_bbox(*spec["center"])
    print(f"building {name} bbox={bbox} crs={metric_crs}")
    graph, buildings, parks, pois, water, landuse = fetch_osm(spec["place"], bbox)
    with tempfile.TemporaryDirectory(prefix=f"{name}_pocket_") as tmp:
        sentinel, dem, raster_meta = fetch_rasters(bbox, Path(tmp))
        from urbancode.area import StudyArea
        from urbancode.city import City

        area = StudyArea.from_bbox(
            *bbox, place=spec["place"], city_id=spec["city_id"]
        )
        city = City(place=spec["place"], study_area=area, metadata={"bbox": list(bbox)})
        city.add_layer("streets", graph, kind="graph", crs="EPSG:4326", source="osm")
        city.add_layer("buildings", buildings, kind="vector", crs="EPSG:4326", source="osm")
        city.add_layer("parks", parks, kind="vector", crs="EPSG:4326", source="osm")
        city.add_layer("pois", pois, kind="vector", crs="EPSG:4326", source="osm")
        city.add_layer("water", water, kind="vector", crs="EPSG:4326", source="osm")
        city.add_layer("landuse", landuse, kind="vector", crs="EPSG:4326", source="osm")
        city.add_layer(
            "sentinel2",
            None,
            kind="raster",
            path=str(sentinel),
            source="sentinel-2-l2a",
            metadata=raster_meta,
        )
        city.add_layer(
            "dem",
            None,
            kind="raster",
            path=str(dem),
            source="cop-dem-glo-30",
        )
        if out.exists():
            shutil.rmtree(out)
        city.to_dir(out, overwrite=True)
    write_sidecar(out, spec, bbox, metric_crs, raster_meta)
    print(f"wrote {out}")
    return out


def check() -> int:
    from data.dataset_manifest import iter_dataset_dirs, validate_real

    errors: list[str] = []
    for path in iter_dataset_dirs(REAL_DATA):
        if path.name in {"climate", "streetview"}:
            errors.extend(validate_real(path))
            continue
        if path.name not in CITIES:
            continue
        errors.extend(validate_real(path))
        data = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        if data.get("synthetic") is True:
            errors.append(f"{path.name}: synthetic real pocket")
        extent = data.get("physical_extent") or {}
        if float(extent.get("width", 0)) != WIDTH_M:
            errors.append(f"{path.name}: physical width is not {WIDTH_M}")
    if errors:
        print("\n".join(errors))
        return 1
    print("real pockets ok")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", choices=sorted(CITIES))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.check:
        return check()
    names = list(CITIES) if args.all else [args.city] if args.city else []
    if not names:
        parser.error("pass --city, --all, or --check")
    REAL_DATA.mkdir(parents=True, exist_ok=True)
    for name in names:
        build_city(name, overwrite=args.overwrite)
    return 0


if __name__ == "__main__":
    sys.exit(main())
