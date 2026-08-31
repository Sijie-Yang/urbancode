"""Staged TCIS inference on the Alienware Singapore SVI store.

Stages: 10 → 100 → 1000 → 92233. The full run is refused until the
100-image stage writes a passing receipt.

    python examples/live/run_tcis_singapore.py --stage 10 \\
        --image-root D:\\svi_singapore_92233_resized_version \\
        --catalog .../tcis_svi_catalog.parquet \\
        --output .../predictions.parquet
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import urbancode as uc
from urbancode.perception.backends.tcis_runtime import peak_gpu_memory_mb

STAGES = (10, 100, 1000, 92233)


def _receipt_path(output: Path, stage: int) -> Path:
    return output.with_name(f"{output.stem}_stage_{stage}.json")


def _require_prior_stage(output: Path, stage: int) -> None:
    required = {100: (10,), 1000: (100,), 92233: (100, 1000)}.get(stage, ())
    for previous in required:
        receipt = _receipt_path(output, previous)
        if not receipt.is_file():
            raise RuntimeError(
                f"stage {stage} requires a passing receipt at {receipt}"
            )
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        if not payload.get("passed"):
            raise RuntimeError(f"stage {previous} receipt is not passed: {receipt}")


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=int, required=True, choices=STAGES)
    parser.add_argument("--image-root", required=True, type=Path)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument(
        "--include-features",
        dest="include_features",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--no-include-features",
        dest="include_features",
        action="store_false",
    )
    args = parser.parse_args(argv)

    _require_prior_stage(args.output, args.stage)
    catalog = pd.read_parquet(args.catalog)
    sample = catalog.head(args.stage).copy()
    images = uc.images.from_table(
        sample,
        id_column="image_id",
        path_column="relative_path",
        lon="longitude",
        lat="latitude",
        view_type="streetview",
        source=sample["provider"] if "provider" in sample.columns else None,
        city_id="singapore",
        image_root=args.image_root,
    )
    t0 = time.perf_counter()
    layer = uc.perception.thermal_affordance(
        images,
        device=args.device,
        batch_size=args.batch_size,
        chunk_size=min(args.chunk_size, args.stage),
        resume=True,
        output=args.output,
        include_features=args.include_features,
        image_root=args.image_root,
    )
    elapsed = time.perf_counter() - t0
    frame = layer.data
    n = int(len(frame))
    failed = int(frame["error"].notna().sum()) if "error" in frame.columns else 0
    success = n - failed
    rate = success / elapsed if elapsed else 0.0
    provenance = (layer.metadata or {}).get("model") or {}
    receipt = {
        "stage": args.stage,
        "passed": failed == 0 and success == args.stage,
        "success": success,
        "failed": failed,
        "images_per_second": round(rate, 3),
        "device": provenance.get("device") or args.device,
        "peak_gpu_memory_mb": peak_gpu_memory_mb(args.device),
        "elapsed_s": round(elapsed, 3),
        "eta_92233_hours": round((92233 / rate) / 3600, 2) if rate else None,
        "output_rows": n,
        "model_revision": provenance.get("model_revision"),
        "segformer_revision": provenance.get("segformer_revision"),
        "weights_sha256": provenance.get("weights_sha256"),
        "finished": datetime.now(timezone.utc).isoformat(),
        "resume": True,
    }
    dest = _receipt_path(args.output, args.stage)
    dest.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return receipt


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
