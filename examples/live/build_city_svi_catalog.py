"""Build an image catalog from an eight-city svi_*.csv plus a photo folder."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def build_catalog(csv_path: Path, image_root: Path, city_id: str) -> pd.DataFrame:
    raw = pd.read_csv(csv_path)
    if "pid" not in raw.columns:
        raise ValueError(f"{csv_path} needs a pid column")
    lat_col = "lat" if "lat" in raw.columns else "latitude"
    lon_col = "lng" if "lng" in raw.columns else "longitude"
    rows = []
    missing = 0
    for row in raw.itertuples(index=False):
        pid = str(getattr(row, "pid"))
        name = f"{pid}.jpg"
        path = image_root / name
        if not path.is_file():
            alt = image_root / f"{pid}.jpeg"
            if alt.is_file():
                name = alt.name
                path = alt
            else:
                missing += 1
                continue
        rows.append(
            {
                "image_id": pid,
                "relative_path": name,
                "longitude": float(getattr(row, lon_col)),
                "latitude": float(getattr(row, lat_col)),
                "heading": getattr(row, "heading", None),
                "captured_at": getattr(row, "date", None),
                "panorama_id": pid,
                "parse_error": None,
            }
        )
    if not rows:
        raise FileNotFoundError(f"no matching images in {image_root}")
    catalog = pd.DataFrame(rows)
    catalog["provider"] = None
    catalog["pitch"] = None
    catalog["fov"] = None
    catalog["license"] = None
    catalog["city_id"] = city_id
    catalog["view_type"] = "streetview"
    catalog.attrs["missing_images"] = missing
    return catalog


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--image-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--city-id", required=True)
    args = parser.parse_args(argv)
    catalog = build_catalog(args.csv, args.image_root, args.city_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    catalog.to_parquet(args.output, index=False)
    return {
        "n": int(len(catalog)),
        "missing_images": int(catalog.attrs.get("missing_images") or 0),
        "output": str(args.output),
    }


if __name__ == "__main__":
    print(main())
