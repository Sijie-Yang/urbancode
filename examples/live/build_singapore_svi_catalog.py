"""Register the existing Alienware Singapore SVI store. Does not download.

Usage on Alienware:

    python examples/live/build_singapore_svi_catalog.py \\
        --image-root D:\\svi_singapore_92233_resized_version \\
        --output examples/data/research_cases/thermal_comfort_in_sight_singapore/tcis_svi_catalog.parquet
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

NAME_RE = re.compile(
    r"^(?P<image_id>[^_]+)_(?P<lon>-?\d+\.\d+)_(?P<lat>-?\d+\.\d+)\.(?P<ext>jpe?g|png)$",
    re.I,
)


def build_catalog(image_root: Path) -> pd.DataFrame:
    rows = []
    for path in sorted(image_root.iterdir()):
        if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        match = NAME_RE.match(path.name)
        if not match:
            rows.append(
                {
                    "image_id": path.stem,
                    "relative_path": path.name,
                    "longitude": None,
                    "latitude": None,
                    "parse_error": "filename_not_id_lon_lat",
                }
            )
            continue
        rows.append(
            {
                "image_id": match.group("image_id"),
                "relative_path": path.name,
                "longitude": float(match.group("lon")),
                "latitude": float(match.group("lat")),
                "parse_error": None,
            }
        )
    if not rows:
        raise FileNotFoundError(f"no images in {image_root}")
    catalog = pd.DataFrame(rows)
    if catalog["image_id"].duplicated().any():
        raise ValueError("duplicate image_id values in catalog")
    catalog["provider"] = None
    catalog["heading"] = None
    catalog["pitch"] = None
    catalog["fov"] = None
    catalog["captured_at"] = None
    catalog["panorama_id"] = None
    catalog["license"] = None
    catalog["city_id"] = "singapore"
    catalog["view_type"] = "streetview"
    return catalog


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    root = args.image_root.expanduser()
    if not root.is_dir():
        raise FileNotFoundError(f"image_root does not exist: {root}")
    catalog = build_catalog(root)
    dest = args.output
    dest.parent.mkdir(parents=True, exist_ok=True)
    catalog.to_parquet(dest, index=False)
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    summary = {
        "n_images": int(len(catalog)),
        "n_geolocated": int(catalog["longitude"].notna().sum()),
        "n_parse_errors": int(catalog["parse_error"].notna().sum()),
        "catalog": dest.name,
        "catalog_sha256": digest,
        "image_root_name": root.name,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "note": "image_root is local to the machine that built this catalog",
    }
    (dest.parent / "catalog_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
