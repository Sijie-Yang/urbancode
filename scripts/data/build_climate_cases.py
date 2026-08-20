#!/usr/bin/env python3
"""Download one Open-Meteo archive timestamp per real city pocket."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_lib import REAL_DATA  # noqa: E402
from data.build_real_pockets import CITIES  # noqa: E402
from data.dataset_manifest import write_checksums  # noqa: E402

STAMP = "2024-07-15T14:00"
USER_AGENT = "UrbanCodeClimate/0.3 (https://github.com/Sijie-Yang/urbancode)"


def fetch_open_meteo(lon: float, lat: float) -> dict:
    params = {
        "latitude": f"{lat:.5f}",
        "longitude": f"{lon:.5f}",
        "start_date": "2024-07-15",
        "end_date": "2024-07-15",
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "wind_speed_unit": "ms",
        "timezone": "UTC",
    }
    url = "https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    try:
        idx = times.index("2024-07-15T14:00")
    except ValueError:
        idx = 14 if len(times) > 14 else 0
    if not times:
        raise RuntimeError(f"Open-Meteo returned no hourly rows for {lat},{lon}")
    return {
        "timestamp": times[idx],
        "air_temperature_c": hourly["temperature_2m"][idx],
        "relative_humidity_percent": hourly["relative_humidity_2m"][idx],
        "wind_speed_ms": hourly["wind_speed_10m"][idx],
        "source": "open-meteo-archive",
        "source_uri": url,
        "units": {
            "air_temperature": "degree_celsius",
            "relative_humidity": "percent",
            "wind_speed": "m s-1",
        },
        "mean_radiant_temperature": {
            "value": hourly["temperature_2m"][idx],
            "status": "modelled",
            "assumption": "MRT set equal to 2 m air temperature (modelled_mrt)",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    out = REAL_DATA / "climate"
    if args.check:
        if not (out / "manifest.json").is_file():
            print("missing climate dataset")
            return 1
        print("climate dataset present")
        return 0
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, spec in CITIES.items():
        lon, lat = spec["center"]
        print(f"climate {name}")
        row = fetch_open_meteo(lon, lat)
        row.update({"city_id": spec["city_id"], "place": spec["place"], "lon": lon, "lat": lat})
        rows.append(row)
    observations = out / "observations.json"
    observations.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    generated = datetime.now(timezone.utc).isoformat()
    manifest = {
        "dataset_id": "climate_real_v1",
        "city_id": "multi",
        "place": "Punggol / Kallio / Greenwich Village",
        "bbox": None,
        "physical_extent": {"width": 0, "height": 0, "unit": "point"},
        "geographic_crs": "EPSG:4326",
        "metric_crs": "EPSG:4326",
        "source": "open-meteo-archive",
        "source_uri": "https://open-meteo.com/",
        "license": "CC BY 4.0 (Open-Meteo)",
        "attribution": "Weather data by Open-Meteo.com (CC BY 4.0)",
        "acquired_at": STAMP,
        "temporal_extent": STAMP,
        "original_item_id": {"open_meteo": STAMP},
        "processing_steps": [
            "Open-Meteo archive hourly extract at 2024-07-15T14:00 UTC",
            "MRT modelled as equal to air temperature (quality flag modelled_mrt)",
        ],
        "file_checksums": {},
        "generated_by": "scripts/data/build_climate_cases.py",
        "generated_at": generated,
        "synthetic": False,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (out / "LICENSE.md").write_text(
        "# Real climate observations\n\n"
        "Hourly archive fields from Open-Meteo (CC BY 4.0).\n"
        "https://open-meteo.com/\n\n"
        "Mean radiant temperature is modelled, not observed.\n",
        encoding="utf-8",
    )
    (out / "README.md").write_text(
        "# Real climate observations\n\n"
        f"One UTC timestamp ({STAMP}) per city center.\n"
        "Fields: air temperature, relative humidity, wind speed.\n"
        "MRT is modelled (equal to air temperature) and must be labelled modelled.\n",
        encoding="utf-8",
    )
    write_checksums(out, [observations, out / "manifest.json", out / "LICENSE.md", out / "README.md"])
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
