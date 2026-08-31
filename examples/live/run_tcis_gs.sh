#!/usr/bin/env bash
# Global Streetscapes TCIS: inventory → filter → copy 1000 → 10/100/1000 gate.
set -euo pipefail

ROOT=/data/sijie/UrbanCode
GS=/mnt/data/global-streetscapes
OUT=/data/sijie/gs
CONDA=/data/sijie/miniconda3
export URBANCODE_CACHE_DIR=/data/sijie/urbancode_cache
export HF_HOME=/data/sijie/hf_home
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED=1

# shellcheck disable=SC1091
source "$CONDA/etc/profile.d/conda.sh"
conda activate uc

mkdir -p "$OUT/tcis" "$OUT/logs"
LOG="$OUT/logs/pipeline.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== START $(date -Is) ==="
python "$ROOT/examples/live/build_gs_catalog.py" walk --gs-root "$GS" --out "$OUT"
python "$ROOT/examples/live/build_gs_catalog.py" catalog --gs-root "$GS" --out "$OUT"
python "$ROOT/examples/live/build_gs_catalog.py" copy-smoke --gs-root "$GS" --out "$OUT" --n 1000

run_stage() {
  local stage=$1
  echo "=== TCIS stage $stage $(date -Is) ==="
  python "$ROOT/examples/live/run_tcis_gs.py" \
    --stage "$stage" \
    --image-root "$OUT/smoke/images" \
    --catalog "$OUT/catalog_smoke.parquet" \
    --output "$OUT/tcis/predictions.parquet" \
    --device cuda \
    --batch-size 8 \
    --chunk-size 1000
}

run_stage 10
run_stage 100
run_stage 1000
echo "=== GATE DONE $(date -Is) ==="
echo "On-disk full run is not started. Inspect $OUT/catalog_summary.json first."
