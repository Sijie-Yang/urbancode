"""TCIS inference contract: column names, stats, and checkpoint checks.

This module is torch-free so unit tests can run without the ``streetview`` extra.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

_DATA_DIR = Path(__file__).resolve().parent / "data"
_MANIFEST_PATH = _DATA_DIR / "tcis_manifest.json"
_FEATURE_MODELS_PATH = _DATA_DIR / "feature_models_manifest.json"


class ContractError(ValueError):
    """The DataFrame, stats file, or checkpoint does not match the TCIS contract."""


def load_manifest(path: Path | None = None) -> dict[str, Any]:
    """Load the bundled TCIS model manifest."""
    manifest_path = path or _MANIFEST_PATH
    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    names = manifest["initial_feature_names"]
    if len(names) != int(manifest["num_initial_features"]):
        raise ContractError(
            f"manifest initial_feature_names has {len(names)} entries, "
            f"expected {manifest['num_initial_features']}"
        )
    heads = manifest["head_feature_names"]
    if len(heads) != int(manifest["num_head_features"]):
        raise ContractError(
            f"manifest head_feature_names has {len(heads)} entries, "
            f"expected {manifest['num_head_features']}"
        )
    return manifest


def load_feature_models_manifest(path: Path | None = None) -> dict[str, Any]:
    """Pinned SegFormer / Faster R-CNN / Places365 revisions for TCIS IF."""
    manifest_path = path or _FEATURE_MODELS_PATH
    with manifest_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def initial_feature_names(manifest: Mapping[str, Any] | None = None) -> list[str]:
    """Return the 59 image-feature column names in training order."""
    data = manifest or load_manifest()
    return list(data["initial_feature_names"])


def output_feature_names(manifest: Mapping[str, Any] | None = None) -> list[str]:
    """Return UrbanCode public output column names."""
    data = manifest or load_manifest()
    return list(data["output_feature_names"])


def missing_initial_features(
    columns: Sequence[str],
    names: Sequence[str] | None = None,
) -> list[str]:
    """Return contract feature names absent from ``columns``."""
    have = set(columns)
    return [name for name in (names or initial_feature_names()) if name not in have]


def initial_features_from_frame(
    frame: Any,
    names: Sequence[str] | None = None,
) -> np.ndarray:
    """Select initial features **by column name**.

    Raises:
        ContractError: if any required column is missing.
    """
    required = list(names or initial_feature_names())
    missing = missing_initial_features(list(frame.columns), required)
    if missing:
        raise ContractError(
            "DataFrame is missing TCIS initial features: "
            + ", ".join(missing)
        )
    values = frame.loc[:, list(required)].to_numpy(dtype=float)
    if values.shape[1] != len(required):
        raise ContractError(
            f"expected {len(required)} initial features, got {values.shape[1]}"
        )
    return values


def load_feature_stats(path: Path, n_features: int) -> tuple[np.ndarray, np.ndarray]:
    """Load min/max stats and verify they match ``n_features``."""
    stats = np.load(path)
    if "mins" not in stats.files or "maxs" not in stats.files:
        raise ContractError(f"{path} must contain 'mins' and 'maxs'")
    mins = np.asarray(stats["mins"], dtype=float)
    maxs = np.asarray(stats["maxs"], dtype=float)
    if mins.shape != (n_features,) or maxs.shape != (n_features,):
        raise ContractError(
            f"feature stats length mismatch: mins{tuple(mins.shape)} "
            f"maxs{tuple(maxs.shape)} vs n_features={n_features}"
        )
    return mins, maxs


def normalize_initial_features(
    values: np.ndarray,
    mins: np.ndarray,
    maxs: np.ndarray,
) -> np.ndarray:
    """Min-max normalize; zero-range columns become 0."""
    span = maxs - mins
    safe = np.where(span == 0, 1.0, span)
    return (values - mins) / safe


def validate_state_dict(
    state: Mapping[str, Any],
    num_initial_features: int = 59,
    num_head_features: int = 20,
) -> None:
    """Check that a checkpoint matches TwoStageNNModel input/output sizes."""
    required = (
        "task_layers.0.weight",
        "task_layers.9.weight",
        "final_layer.0.weight",
        "final_layer.6.weight",
    )
    missing = [key for key in required if key not in state]
    if missing:
        raise ContractError(f"checkpoint missing keys: {missing}")

    task_in = _shape0(state["task_layers.0.weight"], dim=1)
    task_out = _shape0(state["task_layers.9.weight"], dim=0)
    final_out = _shape0(state["final_layer.6.weight"], dim=0)
    # ResNet50 embedding is 2048.
    expected_task_in = 2048 + num_initial_features
    if task_in != expected_task_in:
        raise ContractError(
            f"task_layers input dim {task_in} != {expected_task_in} "
            f"(2048 + {num_initial_features} initial features)"
        )
    if task_out != num_head_features:
        raise ContractError(
            f"task_layers output dim {task_out} != {num_head_features}"
        )
    if final_out != 1:
        raise ContractError(f"final_layer output dim {final_out} != 1")


def _shape0(tensor: Any, dim: int) -> int:
    shape = getattr(tensor, "shape", None)
    if shape is None:
        raise ContractError("checkpoint tensor has no shape")
    return int(shape[dim])
