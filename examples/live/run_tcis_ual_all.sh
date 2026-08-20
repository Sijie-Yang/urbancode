#!/usr/bin/env bash
# 92k first (images already on disk), then eight cities after the copy finishes.
set -euo pipefail

ROOT=/data/sijie/UrbanCode
SVI=/data/sijie/svi_data
OUT=/data/sijie/svi_data/tcis
CONDA=/data/sijie/miniconda3
export URBANCODE_CACHE_DIR=/data/sijie/urbancode_cache
export HF_HOME=/data/sijie/hf_home
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED=1

# shellcheck disable=SC1091
source "$CONDA/etc/profile.d/conda.sh"
conda activate uc

mkdir -p "$OUT" /data/sijie/tcis_runs
LOG=/data/sijie/tcis_runs/all.log
exec > >(tee -a "$LOG") 2>&1

echo "=== START $(date -Is) ==="
python -c "import torch; print('cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)"

wait_count() {
  local dir=$1
  local need=$2
  while true; do
    local n
    n=$(find "$dir" -type f | wc -l | tr -d ' ')
    echo "$(date -Is) wait $dir $n/$need"
    if [[ "$n" -ge "$need" ]]; then
      return 0
    fi
    sleep 60
  done
}

wait_tar_idle() {
  while pgrep -u "$USER" -f "tar -xf - -C /data/sijie/svi_data" >/dev/null 2>&1; do
    echo "$(date -Is) copy still running"
    sleep 60
  done
}

run_one() {
  local name=$1
  local images=$2
  local catalog=$3
  local limit=${4:-0}
  local extra=()
  if [[ "$limit" != "0" ]]; then
    extra+=(--limit "$limit")
  fi
  echo "=== RUN $name $(date -Is) ==="
  python "$ROOT/examples/live/run_tcis_dataset.py" \
    --image-root "$images" \
    --catalog "$catalog" \
    --output "$OUT/$name/predictions.parquet" \
    --device cuda \
    --batch-size 8 \
    --chunk-size 1000 \
    --city-id "$name" \
    "${extra[@]}"
}

# --- 92k Singapore (ready now) ---
if [[ ! -f "$OUT/svi_sg_92233/catalog.parquet" ]]; then
  python "$ROOT/examples/live/build_singapore_svi_catalog.py" \
    --image-root "$SVI/svi_sg_92233" \
    --output "$OUT/svi_sg_92233/catalog.parquet"
fi

if [[ ! -f "$OUT/svi_sg_92233/predictions_stage_smoke.json" ]]; then
  run_one svi_sg_92233 "$SVI/svi_sg_92233" "$OUT/svi_sg_92233/catalog.parquet" 10
  cp "$OUT/svi_sg_92233/predictions_receipt.json" "$OUT/svi_sg_92233/predictions_stage_smoke.json"
fi

run_one svi_sg_92233 "$SVI/svi_sg_92233" "$OUT/svi_sg_92233/catalog.parquet" 0

# --- eight cities after copy ---
wait_tar_idle
declare -A EXPECT=(
  [svi_capetown]=170886
  [svi_hk]=17094
  [svi_jh]=172234
  [svi_melbourne]=226556
  [svi_ny]=54403
  [svi_rio]=55311
  [svi_sg]=21839
  [svi_tokyo]=175816
)
for city in svi_capetown svi_hk svi_jh svi_melbourne svi_ny svi_rio svi_sg svi_tokyo; do
  wait_count "$SVI/$city" "${EXPECT[$city]}"
  if [[ ! -f "$OUT/$city/catalog.parquet" ]]; then
    python "$ROOT/examples/live/build_city_svi_catalog.py" \
      --csv "$SVI/${city}.csv" \
      --image-root "$SVI/$city" \
      --output "$OUT/$city/catalog.parquet" \
      --city-id "$city"
  fi
  run_one "$city" "$SVI/$city" "$OUT/$city/catalog.parquet" 0
done

echo "=== ALL DONE $(date -Is) ==="
