"""Optional TCIS smoke: skip when cached weights are absent."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from urbancode.cache import models_dir
from urbancode.streetview.contract import (
    initial_feature_names,
    initial_features_from_frame,
    load_manifest,
    output_feature_names,
)


def test_manifest_sha_fields() -> None:
    manifest = load_manifest()
    assert len(manifest["weights_sha256"]) == 64
    assert len(manifest["stats_sha256"]) == 64
    assert manifest["hf_dataset"].startswith("sijiey/")
    revision = str(manifest.get("revision") or "")
    assert revision != "main"
    assert len(revision) == 40


def test_comfort_columns_exist_when_weights_cached() -> None:
    weights = models_dir() / "best_model.pth"
    if not weights.exists():
        pytest.skip("TCIS weights not cached")
    pytest.importorskip("torch")
    names = initial_feature_names()
    frame = pd.DataFrame({name: [0.0] for name in names})
    values = initial_features_from_frame(frame)
    assert values.shape == (1, 59)
    assert np.isfinite(values).all()
    assert output_feature_names()[0] == "thermal_comfort"


def test_comfort_golden_image(tmp_path: Path) -> None:
    weights = models_dir() / "best_model.pth"
    require = os.environ.get("UC_FAIL_ON_SKIP") == "1"
    if not weights.exists() and not require:
        pytest.skip("TCIS weights not cached")
    pytest.importorskip("torch")
    pytest.importorskip("PIL")
    from PIL import Image

    from urbancode.streetview.perception import comfort

    img = tmp_path / "golden.png"
    Image.new("RGB", (64, 64), (80, 120, 60)).save(img)
    frame = comfort(str(img), mode="image", device="cpu")
    names = output_feature_names()
    for name in names:
        assert name in frame.columns
        assert np.isfinite(frame[name].iloc[0])
    assert np.isfinite(frame["thermal_comfort"].iloc[0])
    for name in initial_feature_names():
        assert name in frame.columns
        assert np.isfinite(frame[name].iloc[0])
