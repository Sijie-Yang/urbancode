"""Run TCIS on a catalog. Writes IF + VPI + VATA parquet."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import urbancode as uc
from urbancode.perception.backends.tcis_runtime import peak_gpu_memory_mb


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-root", required=True, type=Path)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--city-id", default=None)
    args = parser.parse_args(argv)

    city = args.city_id or ""
    if city not in {"svi_capetown", "svi_sg_92233", ""}:
        gate = Path("/data/sijie/tcis_runs/resize.done")
        while not gate.is_file():
            print(f"waiting for resize.done before {city}", flush=True)
            time.sleep(30)

    catalog = pd.read_parquet(args.catalog)
    if args.limit:
        catalog = catalog.head(args.limit).copy()
    images = uc.images.from_table(
        catalog,
        id_column="image_id",
        path_column="relative_path",
        lon="longitude",
        lat="latitude",
        view_type="streetview",
        city_id=args.city_id or catalog["city_id"].iloc[0] if "city_id" in catalog.columns else None,
        image_root=args.image_root,
    )
    t0 = time.perf_counter()
    layer = uc.perception.thermal_affordance(
        images,
        device=args.device,
        batch_size=args.batch_size,
        chunk_size=args.chunk_size,
        resume=True,
        output=args.output,
        include_features=True,
        image_root=args.image_root,
    )
    elapsed = time.perf_counter() - t0
    frame = layer.data
    n = int(len(frame))
    failed = int(frame["error"].notna().sum()) if "error" in frame.columns else 0
    success = n - failed
    rate = success / elapsed if elapsed else 0.0
    receipt = {
        "catalog": str(args.catalog),
        "image_root": str(args.image_root),
        "output": str(args.output),
        "success": success,
        "failed": failed,
        "n_columns": int(len(frame.columns)),
        "has_if": "seg_road" in frame.columns,
        "has_vpi": "visual_comfort" in frame.columns,
        "images_per_second": round(rate, 3),
        "device": args.device,
        "peak_gpu_memory_mb": peak_gpu_memory_mb(args.device),
        "elapsed_s": round(elapsed, 3),
        "finished": datetime.now(timezone.utc).isoformat(),
    }
    dest = args.output.with_name(f"{args.output.stem}_receipt.json")
    dest.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return receipt


if __name__ == "__main__":
    main()
