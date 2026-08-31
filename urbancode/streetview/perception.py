"""Compatibility TCIS entry. Prefer ``uc.perception.thermal_affordance``."""

from __future__ import annotations

import os
import warnings
from typing import Any

import pandas as pd

from urbancode.perception.backends.tcis import (
    CANONICAL_SCORE,
    LEGACY_SCORE,
    predict_frame,
    predict_paths,
)


def comfort(img_path, mode="image", device=None):
    """Predict TCIS scores and return a DataFrame (deprecated).

    Prefer :func:`urbancode.perception.thermal_affordance`, which returns
    a Layer. ``thermal_comfort`` remains as a one-cycle alias of
    ``thermal_affordance`` (VATA). It is not measured personal comfort
    and it is not UTCI.

    Args:
        img_path: Path to an image file or a folder of images.
        mode: ``'image'`` or ``'folder'``.
        device: ``'cuda'``, ``'cpu'``, or ``None`` (auto).

    Returns:
        DataFrame with legacy ``thermal_comfort`` plus VPI columns.
    """
    warnings.warn(
        "uc.streetview.comfort() is deprecated and returns a DataFrame. "
        "Use uc.perception.thermal_affordance() to stay on the Layer → "
        "AnalysisUnits → IndicatorResult path. thermal_comfort is a "
        "compatibility alias for thermal_affordance (VATA), not measured "
        "comfort and not UTCI.",
        DeprecationWarning,
        stacklevel=2,
    )
    if mode not in ["image", "folder"]:
        raise ValueError("mode must be either 'image' or 'folder'")

    if mode == "image":
        frame = predict_paths(
            [img_path], device=device, include_features=True
        )
    else:
        from urbancode.streetview import features as sv_features

        catalog = sv_features.filename(img_path)
        catalog = catalog.copy()
        catalog["image_path"] = [
            os.path.join(img_path, name) for name in catalog["Filename"]
        ]
        frame = predict_frame(
            catalog,
            folder_path=img_path,
            device=device,
            include_features=True,
        )

    if CANONICAL_SCORE in frame.columns and LEGACY_SCORE not in frame.columns:
        frame[LEGACY_SCORE] = frame[CANONICAL_SCORE]
    return frame


def __getattr__(name: str) -> Any:
    if name in {
        "TwoStageNNModel",
        "CustomDataset",
        "TwoStageNNPerception",
        "compute_metrics",
    }:
        raise AttributeError(
            f"{name} was a training helper and is not part of the public "
            "UrbanCode API. Inference lives in "
            "urbancode.perception.thermal_affordance."
        )
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
