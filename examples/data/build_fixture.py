"""Build the committed Punggol City fixture from live OSM / STAC / Commons.

CI does not run this. Re-run locally when the extract should be refreshed.
Helsinki and NYC pockets: ``python examples/data/build_pockets.py``.
"""

from __future__ import annotations

import json
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from shapely.geometry import box

ROOT = Path(__file__).resolve().parent / "punggol_pocket"
BBOX = (103.905, 1.400, 103.915, 1.410)
TITLE = "Punggol, Singapore"
USER_AGENT = "UrbanCodeFixture/0.3 (https://github.com/Sijie-Yang/urbancode)"


def _clip(gdf, bbox: tuple[float, float, float, float]):
    import geopandas as gpd

    west, south, east, north = bbox
    frame = gdf.to_crs("EPSG:4326") if gdf.crs is not None else gdf.set_crs("EPSG:4326")
    clipped = gpd.clip(frame, box(west, south, east, north))
    return clipped[~clipped.geometry.is_empty].copy()


def _slim(gdf, columns: list[str]):
    keep = [c for c in columns if c in gdf.columns]
    out = gdf[keep + ["geometry"]].copy() if keep else gdf[["geometry"]].copy()
    return out


def _fetch_osm():
    import osmnx as ox
    from urbancode.network.fetch import fetch as network_fetch

    ox.settings.timeout = 180
    city = network_fetch(
        place=TITLE,
        bbox=BBOX,
        layers=["streets", "buildings", "parks", "pois"],
        network_type="walk",
        use_cache=True,
    )
    if city.errors:
        raise RuntimeError(f"OSM fetch errors: {city.errors}")
    buildings = _slim(_clip(city["buildings"], BBOX), ["name", "building"])
    parks = _slim(_clip(city["parks"], BBOX), ["name", "leisure", "natural"])
    pois = _slim(_clip(city["pois"], BBOX), ["name", "amenity", "shop", "tourism"])
    if buildings.empty or parks.empty or pois.empty:
        raise RuntimeError(
            f"empty layer after clip: buildings={len(buildings)} "
            f"parks={len(parks)} pois={len(pois)}"
        )
    return city["streets"], buildings, parks, pois


def _fetch_rasters(tmp: Path) -> tuple[Path, Path, dict]:
    from urbancode.imagery.grid import reproject_to_reference, stack_to_reference
    from urbancode.imagery.stac import (
        DEM_COLLECTION,
        SENTINEL2_COLLECTION,
        default_time_range,
        download_assets_windowed,
        search_items,
    )

    interval = default_time_range()
    items = search_items(SENTINEL2_COLLECTION, BBOX, datetime=interval, cloud=40)
    optical = download_assets_windowed(
        items[:1],
        ["B04", "B08", "B11"],
        tmp / "sentinel",
        BBOX,
        max_pixels=2_000_000,
    )
    stacked = stack_to_reference(
        {name: optical[name] for name in ("B04", "B08", "B11") if name in optical},
        tmp / "sentinel2.tif",
        reference="B08",
    )
    dem_items = search_items(DEM_COLLECTION, BBOX, datetime=None, cloud=None)
    dem_assets = download_assets_windowed(
        dem_items[:1],
        ["data"],
        tmp / "dem",
        BBOX,
        max_pixels=2_000_000,
    )
    dem = reproject_to_reference(
        next(iter(dem_assets.values())),
        tmp / "dem.tif",
        reference_path=stacked,
        resampling="bilinear",
    )
    meta = {
        "sentinel_item_ids": [it.id for it in items[:1]],
        "sentinel_datetime": items[0].properties.get("datetime") if items else None,
        "dem_item_ids": [it.id for it in dem_items[:1]],
        "time": interval,
    }
    return stacked, dem, meta


def _download_streetview(dest: Path) -> dict[str, str]:
    queries = (
        "Punggol Waterway Park",
        "Punggol Waterway Singapore",
        "Punggol Singapore street",
    )
    for query in queries:
        info = _commons_image(query)
        if info:
            req = urllib.request.Request(info["url"], headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as resp:
                dest.write_bytes(resp.read())
            return info
    raise FileNotFoundError("no Wikimedia Commons still image for Punggol")


def _commons_image(query: str) -> dict[str, str] | None:
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": "8",
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|mime|size",
        "iiurlwidth": "1280",
        "format": "json",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    pages = (payload.get("query") or {}).get("pages") or {}
    for page in pages.values():
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        mime = str(info.get("mime") or "")
        if not mime.startswith("image/") or mime == "image/svg+xml":
            continue
        meta = info.get("extmetadata") or {}
        license_name = (meta.get("LicenseShortName") or {}).get("value", "")
        artist = (meta.get("Artist") or {}).get("value", "")
        credit = (meta.get("Credit") or {}).get("value", "")
        title = page.get("title", "")
        thumb = info.get("thumburl") or info.get("url")
        if not thumb:
            continue
        return {
            "url": thumb,
            "page": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(title)}",
            "title": title,
            "license": license_name,
            "artist": artist,
            "credit": credit,
        }
    return None


def _comfort_frame(photo_meta: dict[str, str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Filename": ["streetview.jpg"],
            "thermal_comfort": [float("nan")],
            "visual_comfort": [float("nan")],
            "model_version": [""],
            "generated_at": [""],
            "photo_page": [photo_meta.get("page", "")],
            "photo_license": [photo_meta.get("license", "")],
            "note": [
                "Real Wikimedia photo. TCIS scores are not baked in; "
                "run examples/live/03_streetview_predict.py"
            ],
        }
    )


def main() -> Path:
    from urbancode.city import City

    graph, buildings, parks, pois = _fetch_osm()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sentinel, dem, raster_meta = _fetch_rasters(tmp_path)
        photo = tmp_path / "streetview.jpg"
        photo_meta = _download_streetview(photo)
        city = City(place=TITLE, metadata={"fixture": True, "bbox": list(BBOX)})
        city.add_layer("streets", graph, kind="graph", crs="EPSG:4326", source="osm")
        city.add_layer(
            "buildings", buildings, kind="vector", crs="EPSG:4326", source="osm"
        )
        city.add_layer("parks", parks, kind="vector", crs="EPSG:4326", source="osm")
        city.add_layer("pois", pois, kind="vector", crs="EPSG:4326", source="osm")
        city.add_layer(
            "sentinel2",
            None,
            kind="raster",
            path=str(sentinel),
            crs="EPSG:32648",
            source="sentinel-2-l2a",
            metadata=raster_meta,
        )
        city.add_layer(
            "dem",
            None,
            kind="raster",
            path=str(dem),
            crs="EPSG:32648",
            source="cop-dem-glo-30",
        )
        city.add_layer(
            "streetview",
            None,
            kind="images",
            path=str(photo),
            source="wikimedia-commons",
            metadata=photo_meta,
        )
        city.add_layer(
            "comfort",
            _comfort_frame(photo_meta),
            kind="table",
            source="display",
        )
        city.to_dir(ROOT, overwrite=True)

    parquet = ROOT / "layers" / "comfort.parquet"
    if parquet.exists():
        frame = pd.read_parquet(parquet)
        frame.to_csv(ROOT / "layers" / "comfort.csv", index=False)
        parquet.unlink()
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        for record in manifest.get("layers") or []:
            if record.get("name") == "comfort":
                record["path"] = "layers/comfort.csv"
        (ROOT / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

    generated = datetime.now(timezone.utc).isoformat()
    (ROOT / "fixture_metadata.json").write_text(
        json.dumps(
            {
                "fixture_version": 2,
                "location": TITLE,
                "title": TITLE,
                "bbox": list(BBOX),
                "geometry_source": "osm",
                "raster_source": "sentinel-2-l2a / cop-dem-glo-30",
                "generated_by": "examples/data/build_fixture.py",
                "generated_at": generated,
                "crs": {"vectors": "EPSG:4326", "rasters": "EPSG:32648"},
                "attribution": {
                    "osm": "© OpenStreetMap contributors (ODbL 1.0)",
                    "sentinel2": "Copernicus Sentinel-2 L2A via Planetary Computer",
                    "dem": "Copernicus DEM GLO-30 via Planetary Computer",
                    "streetview": photo_meta,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (ROOT / "LICENSE.md").write_text(
        f"# {TITLE}\n\n"
        "Real extract for UrbanCode docs and tests. Not a city-wide dump.\n\n"
        "## OpenStreetMap\n\n"
        "© OpenStreetMap contributors. Licensed under ODbL 1.0.\n"
        "https://www.openstreetmap.org/copyright\n\n"
        "## Sentinel-2\n\n"
        "Copernicus Sentinel-2 L2A, accessed via Microsoft Planetary Computer.\n\n"
        "## DEM\n\n"
        "Copernicus DEM GLO-30, accessed via Microsoft Planetary Computer.\n\n"
        "## Street-level photo\n\n"
        f"{photo_meta.get('title', '')}\n"
        f"{photo_meta.get('page', '')}\n"
        f"License: {photo_meta.get('license', '')}\n"
        f"{photo_meta.get('artist', '')}\n",
        encoding="utf-8",
    )
    return ROOT


if __name__ == "__main__":
    print(main())
