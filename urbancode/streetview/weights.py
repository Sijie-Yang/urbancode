"""Download and cache TCIS weights. Does not write into site-packages."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

from urbancode.cache import huggingface_dir, models_dir
from urbancode.streetview.contract import (
    ContractError,
    load_feature_stats,
    load_manifest,
    validate_state_dict,
)

HF_WEIGHT_NAME = "best_model.pth"
HF_STATS_NAME = "feature_stats.npz"
BUNDLED_STATS = Path(__file__).resolve().parent / "data" / "feature_stats.npz"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hf_download(repo_id: str, filename: str, *, repo_type: str, revision: str) -> Path:
    from huggingface_hub import hf_hub_download

    path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        repo_type=repo_type,
        revision=revision,
        cache_dir=str(huggingface_dir()),
    )
    return Path(path)


def _atomic_copy(src: Path, dest: Path, expected_sha: str | None) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    shutil.copy2(src, tmp)
    if expected_sha:
        actual = _sha256(tmp)
        if actual != expected_sha:
            tmp.unlink(missing_ok=True)
            raise ContractError(
                f"SHA-256 mismatch for {dest.name}: got {actual}, expected {expected_sha}"
            )
    os.replace(tmp, dest)
    return dest


def _write_sidecar(dest_dir: Path, manifest: dict) -> None:
    payload = {
        "repo_id": manifest.get("hf_dataset"),
        "revision": manifest.get("revision"),
        "weights_sha256": manifest.get("weights_sha256"),
        "stats_sha256": manifest.get("stats_sha256"),
        "model_version": manifest.get("model_version"),
    }
    (dest_dir / "tcis_bundle.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def ensure_tcis_artifacts(
    *,
    refresh: bool = False,
    dest_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Return ``(weights_path, stats_path)`` from one HF revision.

    Weights and stats are downloaded to a temp dir, SHA-256 checked, then
    atomically moved into the cache. The packaged ``feature_stats.npz`` is
    never overwritten.
    """
    manifest = load_manifest()
    n_features = int(manifest["num_initial_features"])
    revision = str(manifest.get("revision") or "main")
    dataset = str(manifest.get("hf_dataset") or "sijiey/Thermal-Affordance-Dataset")
    model_repo = str(manifest.get("hf_model") or "sijiey/Thermal-Affordance-Model")
    out_dir = dest_dir or models_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    weights_dest = out_dir / manifest["weights_file"]
    stats_dest = out_dir / manifest["stats_file"]
    weights_sha = manifest.get("weights_sha256")
    stats_sha = manifest.get("stats_sha256")

    if weights_dest.exists() and stats_dest.exists() and not refresh:
        ok = True
        if weights_sha and _sha256(weights_dest) != weights_sha:
            ok = False
        if stats_sha and _sha256(stats_dest) != stats_sha:
            ok = False
        if ok:
            load_feature_stats(stats_dest, n_features)
            return weights_dest, stats_dest
        refresh = True

    try:
        weight_src = _hf_download(
            dataset,
            f"model_outputs/{HF_WEIGHT_NAME}",
            repo_type="dataset",
            revision=revision,
        )
        stats_src = _hf_download(
            dataset,
            f"model_outputs/{HF_STATS_NAME}",
            repo_type="dataset",
            revision=revision,
        )
    except Exception as dataset_exc:
        try:
            weight_src = _hf_download(
                model_repo,
                HF_WEIGHT_NAME,
                repo_type="model",
                revision=revision,
            )
            try:
                stats_src = _hf_download(
                    model_repo,
                    HF_STATS_NAME,
                    repo_type="model",
                    revision=revision,
                )
            except Exception:
                if BUNDLED_STATS.exists() and (
                    not stats_sha or _sha256(BUNDLED_STATS) == stats_sha
                ):
                    stats_src = BUNDLED_STATS
                else:
                    raise
        except Exception as model_exc:
            raise FileNotFoundError(
                "Failed to download the TCIS weight+stats bundle from the same "
                f"revision {revision!r}. Dataset error: {dataset_exc}. "
                f"Model error: {model_exc}"
            ) from model_exc

    _atomic_copy(weight_src, weights_dest, weights_sha)
    _atomic_copy(stats_src, stats_dest, stats_sha)
    load_feature_stats(stats_dest, n_features)
    _write_sidecar(out_dir, manifest)
    return weights_dest, stats_dest


def load_validated_state_dict(weights_path: Path, map_location: str = "cpu"):
    """Load a checkpoint and verify it matches the TCIS architecture."""
    from urbancode.errors import require_extra

    torch = require_extra("torch", "svi")
    manifest = load_manifest()
    state = torch.load(weights_path, map_location=map_location)
    if not isinstance(state, dict):
        raise ContractError(f"{weights_path} is not a state_dict")
    if "state_dict" in state and not any(
        key.startswith("task_layers") for key in state
    ):
        state = state["state_dict"]
    validate_state_dict(
        state,
        num_initial_features=int(manifest["num_initial_features"]),
        num_head_features=int(manifest["num_head_features"]),
    )
    return state
