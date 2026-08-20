#!/usr/bin/env bash
set -euo pipefail
CONDA=/data/sijie/miniconda3
# shellcheck disable=SC1091
source "$CONDA/etc/profile.d/conda.sh"
if ! conda env list | awk '{print $1}' | grep -qx uc; then
  conda create -n uc python=3.12 -y
fi
conda activate uc
python -m pip install -U pip
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
cd /data/sijie/UrbanCode
python -m pip install -e ".[perception,vector]"
python -m pip install transformers accelerate safetensors pyarrow
python - <<'PY'
import torch
print("torch", torch.__version__)
print("cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
    x = torch.zeros(1, device="cuda")
    print("tensor_ok", x.device)
PY
