"""Build Helsinki and NYC pocket fixtures (same layer set as Punggol).

Default is a clearly marked synthetic extract so CI stays offline.
Pass ``--live`` locally to try OSM / STAC (not used in tests).
"""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from urbancode.area import StudyArea, utm_crs_from_lonlat
from urbancode.city import City

ROOT = Path(__file__).resolve().parent

POCKETS = {
    "helsinki": {
        "slug": "contracts/helsinki_synthetic",
        "place": "Kallio, Helsinki",
        "city_id": "helsinki",
        "bbox": (24.945, 60.183, 24.955, 60.193),
    },
    "nyc": {
        "slug": "contracts/nyc_synthetic",
        "place": "Greenwich Village, New York",
        "city_id": "nyc",
        "bbox": (-74.005, 40.728, -73.995, 40.738),
    },
}

# Minimal JPEG placeholder (not a real street photo).
_JPEG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000ffdb00430008060607060508"
    "0707070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720"
    "222c231c1c2837292c30313434341f27393d38323c2e333432ffc0000b080001"
    "000101011100ffc40014100100000000000000000000000000000000ffda0008"
    "0001000100003f00fbffd9"
)


def write_synthetic_pocket(spec: dict) -> Path:
    """Write one ~0.01° pocket with the Punggol layer set."""
    import geopandas as gpd
    import networkx as nx
    import rasterio
    from rasterio.transform import from_bounds
    from shapely.geometry import Point, box

    west, south, east, north = spec["bbox"]
    area = StudyArea.from_bbox(*spec["bbox"], place=spec["place"], city_id=spec["city_id"])
    out = ROOT / spec["slug"]
    tmp = Path(tempfile.mkdtemp(prefix=f"{spec['city_id']}_pocket_"))

    city = City(area)
    city.metadata["bbox"] = list(spec["bbox"])
    city.metadata["fixture"] = True
    city.metadata["synthetic"] = True

    nodes = [
        (1, west + 0.002, south + 0.002),
        (2, west + 0.005, south + 0.002),
        (3, west + 0.008, south + 0.002),
        (4, west + 0.002, south + 0.005),
        (5, west + 0.005, south + 0.005),
        (6, west + 0.008, south + 0.005),
        (7, west + 0.002, south + 0.008),
        (8, west + 0.005, south + 0.008),
        (9, west + 0.008, south + 0.008),
    ]
    graph = nx.MultiDiGraph(crs="EPSG:4326")
    for nid, x, y in nodes:
        graph.add_node(nid, x=float(x), y=float(y), street_count=2)
    edges = [(1, 2), (2, 3), (4, 5), (5, 6), (7, 8), (8, 9), (1, 4), (4, 7), (2, 5), (5, 8), (3, 6), (6, 9)]
    for u, v in edges:
        graph.add_edge(u, v, length=80.0, highway="residential", osmid=int(u * 10 + v))
        graph.add_edge(v, u, length=80.0, highway="residential", osmid=int(v * 10 + u))
    city.add_layer("streets", graph, kind="graph", crs="EPSG:4326", source="synthetic")

    pad = 0.0015
    buildings = gpd.GeoDataFrame(
        {"name": ["a", "b"], "building": ["yes", "yes"]},
        geometry=[
            box(west + pad, south + pad, west + 0.003, south + 0.003),
            box(east - 0.003, north - 0.003, east - pad, north - pad),
        ],
        crs="EPSG:4326",
    )
    parks = gpd.GeoDataFrame(
        {"name": ["park"], "leisure": ["park"]},
        geometry=[box(west + 0.004, south + 0.004, west + 0.007, south + 0.007)],
        crs="EPSG:4326",
    )
    pois = gpd.GeoDataFrame(
        {"name": ["cafe"], "amenity": ["cafe"]},
        geometry=[Point(west + 0.005, south + 0.005)],
        crs="EPSG:4326",
    )
    city.add_layer("buildings", buildings, kind="vector", crs="EPSG:4326", source="synthetic")
    city.add_layer("parks", parks, kind="vector", crs="EPSG:4326", source="synthetic")
    city.add_layer("pois", pois, kind="vector", crs="EPSG:4326", source="synthetic")

    metric = area.metric_crs or utm_crs_from_lonlat((west + east) / 2.0, (south + north) / 2.0)
    envelope = gpd.GeoDataFrame(geometry=[box(west, south, east, north)], crs="EPSG:4326").to_crs(metric)
    minx, miny, maxx, maxy = envelope.total_bounds
    width = height = 48
    transform = from_bounds(minx, miny, maxx, maxy, width, height)
    rng = np.random.default_rng(35 if spec["city_id"] == "helsinki" else 18)
    red = rng.uniform(0.05, 0.25, (height, width)).astype("float32")
    nir = rng.uniform(0.20, 0.55, (height, width)).astype("float32")
    swir = rng.uniform(0.10, 0.35, (height, width)).astype("float32")
    dem = rng.uniform(5.0, 40.0, (height, width)).astype("float32")
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 3,
        "dtype": "float32",
        "crs": metric,
        "transform": transform,
        "nodata": float("nan"),
    }
    sentinel_path = tmp / "sentinel2.tif"
    with rasterio.open(sentinel_path, "w", **profile) as dst:
        dst.write(red, 1)
        dst.write(nir, 2)
        dst.write(swir, 3)
        dst.set_band_description(1, "B04")
        dst.set_band_description(2, "B08")
        dst.set_band_description(3, "B11")
    dem_path = tmp / "dem.tif"
    dem_profile = dict(profile, count=1)
    with rasterio.open(dem_path, "w", **dem_profile) as dst:
        dst.write(dem, 1)
    city.add_layer(
        "sentinel2",
        None,
        kind="raster",
        path=str(sentinel_path),
        crs=metric,
        source="synthetic",
        lazy=True,
    )
    city.add_layer(
        "dem",
        None,
        kind="raster",
        path=str(dem_path),
        crs=metric,
        source="synthetic",
        lazy=True,
    )

    photo = tmp / "streetview.jpg"
    photo.write_bytes(_JPEG)
    city.add_layer(
        "streetview",
        None,
        kind="images",
        path=str(photo),
        source="synthetic",
        metadata={"note": "Placeholder JPEG. Not a real street photo."},
    )
    comfort = pd.DataFrame(
        {
            "Filename": ["streetview.jpg"],
            "thermal_comfort": [np.nan],
            "visual_comfort": [np.nan],
            "note": ["Synthetic pocket. TCIS scores are not baked in."],
        }
    )
    city.add_layer("comfort", comfort, kind="table", source="display")

    dest = city.to_dir(out, overwrite=True)
    (dest / "LICENSE.md").write_text(
        f"# {spec['place']}\n\n"
        "Synthetic ~0.01° pocket for UrbanCode offline tests. "
        "Not an OSM / Sentinel / DEM extract. Geometry and rasters "
        "are generated so CI never live-fetches.\n",
        encoding="utf-8",
    )
    (dest / "fixture_metadata.json").write_text(
        json.dumps(
            {
                "fixture_version": 1,
                "location": spec["place"],
                "bbox": list(spec["bbox"]),
                "synthetic": True,
                "generated_by": "examples/data/build_pockets.py",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "crs": {"vectors": "EPSG:4326", "rasters": metric},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return dest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="Try OSM/STAC (local only). Default writes synthetic pockets.",
    )
    args = parser.parse_args()
    if args.live:
        raise SystemExit("live pocket fetch is not wired; omit --live for synthetic")
    for spec in POCKETS.values():
        path = write_synthetic_pocket(spec)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
