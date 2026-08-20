#!/usr/bin/env python3
"""Collect redistributable geotagged Wikimedia Commons photos in each pocket."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_lib import REAL_DATA  # noqa: E402
from data.build_real_pockets import CITIES, metric_bbox  # noqa: E402
from data.dataset_manifest import write_checksums  # noqa: E402

USER_AGENT = "UrbanCodeStreetview/0.3 (https://github.com/Sijie-Yang/urbancode)"
ALLOWED = {"cc by", "cc by-sa", "cc0", "public domain", "cc by 2.0", "cc by 3.0", "cc by 4.0", "cc by-sa 2.0", "cc by-sa 3.0", "cc by-sa 4.0"}


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())


def commons_geosearch(bbox: tuple[float, float, float, float], limit: int = 20) -> list[dict]:
    west, south, east, north = bbox
    params = {
        "action": "query",
        "list": "geosearch",
        "gsbbox": f"{north}|{west}|{south}|{east}",
        "gsnamespace": "6",
        "gslimit": str(limit),
        "format": "json",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    payload = _get(url)
    return list((payload.get("query") or {}).get("geosearch") or [])


def image_info(titles: list[str]) -> list[dict]:
    if not titles:
        return []
    params = {
        "action": "query",
        "titles": "|".join(titles),
        "prop": "imageinfo|coordinates",
        "iiprop": "url|extmetadata|mime|size|sha1",
        "iiurlwidth": "1280",
        "format": "json",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    pages = ((_get(url).get("query") or {}).get("pages") or {}).values()
    return list(pages)


def _license_ok(name: str) -> bool:
    return name.strip().lower() in ALLOWED or name.strip().lower().startswith("cc by")


def collect_city(name: str, spec: dict, dest: Path) -> list[dict]:
    bbox, _ = metric_bbox(*spec["center"])
    hits = commons_geosearch(bbox)
    titles = [hit.get("title") for hit in hits if hit.get("title")]
    records = []
    city_dir = dest / name
    city_dir.mkdir(parents=True, exist_ok=True)
    for page in image_info(titles):
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        mime = str(info.get("mime") or "")
        if not mime.startswith("image/") or mime == "image/svg+xml":
            continue
        meta = info.get("extmetadata") or {}
        license_name = (meta.get("LicenseShortName") or {}).get("value", "")
        if not _license_ok(license_name):
            continue
        coords = page.get("coordinates") or []
        lat = lon = None
        if coords:
            lat = coords[0].get("lat")
            lon = coords[0].get("lon")
        geo = next((hit for hit in hits if hit.get("title") == page.get("title")), None)
        if lat is None and geo:
            lat, lon = geo.get("lat"), geo.get("lon")
        if lat is None or lon is None:
            continue
        title = page.get("title") or "File:unknown"
        slug = title.replace("File:", "").replace(" ", "_")
        safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in slug)[:80]
        filename = f"{safe}.jpg"
        path = city_dir / filename
        thumb = info.get("thumburl") or info.get("url")
        _download(thumb, path)
        records.append(
            {
                "image_id": safe,
                "city_id": spec["city_id"],
                "source": "wikimedia-commons",
                "source_url": info.get("descriptionurl") or info.get("url"),
                "page": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(title)}",
                "license": license_name,
                "author": (meta.get("Artist") or {}).get("value", ""),
                "capture_time": (meta.get("DateTimeOriginal") or {}).get("value"),
                "latitude": lat,
                "longitude": lon,
                "heading": None,
                "field_of_view": None,
                "location_accuracy": "commons-geosearch",
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
                "checksum": hashlib.sha256(path.read_bytes()).hexdigest(),
                "path": f"{name}/{filename}",
            }
        )
        if len(records) >= 8:
            break
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    out = REAL_DATA / "streetview"
    if args.check:
        if not (out / "catalog.json").is_file():
            print("missing streetview catalog")
            return 1
        print("streetview catalog present")
        return 0
    out.mkdir(parents=True, exist_ok=True)
    catalog = []
    for name, spec in CITIES.items():
        print(f"streetview {name}")
        catalog.extend(collect_city(name, spec, out))
    (out / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    generated = datetime.now(timezone.utc).isoformat()
    manifest = {
        "dataset_id": "streetview_real_v1",
        "city_id": "multi",
        "place": "Punggol / Kallio / Greenwich Village",
        "bbox": None,
        "physical_extent": {"width": 2000, "height": 2000, "unit": "metre"},
        "geographic_crs": "EPSG:4326",
        "metric_crs": "local UTM per city",
        "source": "wikimedia-commons",
        "source_uri": "https://commons.wikimedia.org/",
        "license": "per-image Creative Commons, see catalog.json",
        "attribution": "Wikimedia Commons photographers; licenses in catalog.json",
        "acquired_at": generated,
        "temporal_extent": "per-image",
        "original_item_id": [row["image_id"] for row in catalog],
        "processing_steps": [
            "Commons geosearch inside each 2 km pocket",
            "Keep CC BY / CC BY-SA / CC0 / public domain still images",
            "Store 1280 px thumbnail plus lat/lon from Commons",
        ],
        "file_checksums": {},
        "generated_by": "scripts/data/build_streetview_cases.py",
        "generated_at": generated,
        "synthetic": False,
        "n_images": len(catalog),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (out / "LICENSE.md").write_text(
        "# Street-view photo sample\n\n"
        "Images from Wikimedia Commons. Each file keeps its original license.\n"
        "See catalog.json for author, URL, and license.\n",
        encoding="utf-8",
    )
    (out / "README.md").write_text(
        "# Street-view photo sample\n\n"
        f"{len(catalog)} geotagged Commons photos inside the three 2 km pockets.\n"
        "Coordinates come from Commons geosearch, not from a bbox centre.\n"
        "If a city has fewer than 3 photos, spatial recipes for that city stay blocked.\n",
        encoding="utf-8",
    )
    files = [path for path in out.rglob("*") if path.is_file() and path.name != "checksums.sha256"]
    write_checksums(out, files)
    print(f"wrote {len(catalog)} photos to {out}")
    if len(catalog) < 3:
        print("WARNING: fewer than 3 geotagged photos; spatial cases may be blocked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
