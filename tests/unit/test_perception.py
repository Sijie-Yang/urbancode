from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

import urbancode as uc
from urbancode.city import Layer
from urbancode.perception.backends.tcis import CANONICAL_SCORE, LEGACY_SCORE
from urbancode.streetview.contract import load_manifest, output_feature_names


def test_import_perception_does_not_load_torch() -> None:
    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root) + os.pathsep + env.get("PYTHONPATH", "")
    code = (
        "import sys, urbancode as uc; "
        "assert uc.perception.thermal_affordance; "
        "assert 'torch' not in sys.modules"
    )
    subprocess.check_call([sys.executable, "-c", code], env=env)


def test_manifest_names_canonical_score() -> None:
    manifest = load_manifest()
    assert manifest["canonical_score"] == CANONICAL_SCORE
    assert manifest["legacy_score_alias"] == LEGACY_SCORE
    assert output_feature_names()[0] == LEGACY_SCORE
    assert "weights_sha256" in manifest
    assert len(manifest["weights_sha256"]) == 64


def test_thermal_affordance_returns_layer(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("geopandas")
    frame = pd.DataFrame(
        {
            "image_id": ["p1"],
            "image_path": ["p1.jpg"],
            "Filename": ["p1.jpg"],
            "longitude": [103.91],
            "latitude": [1.406],
            CANONICAL_SCORE: [3.2],
            LEGACY_SCORE: [3.2],
            "visual_comfort": [2.8],
            "shading_area": [3.1],
        }
    )
    frame.attrs["tcis_provenance"] = {
        "model_id": "tcis-twostage-resnet50",
        "model_version": "tcis-code4",
        "weights_sha256": "abc",
        "feature_stats_sha256": "def",
        "training_geography": "Singapore",
        "device": "cpu",
        "output_unit": "score_0_5",
    }

    def fake_predict(data, **_kwargs):
        return frame

    monkeypatch.setattr(
        "urbancode.perception.predict.run_dataset", fake_predict
    )
    images = uc.images.from_table(
        pd.DataFrame(
            {
                "image_id": ["p1"],
                "image_path": ["p1.jpg"],
                "longitude": [103.91],
                "latitude": [1.406],
            }
        ),
        view_type="streetview",
    )
    result = uc.perception.thermal_affordance(images, device="cpu")
    assert isinstance(result, Layer)
    assert result.kind == "vector"
    assert CANONICAL_SCORE in result.data.columns
    assert result.metadata["column"] == CANONICAL_SCORE
    assert result.metadata["unit"] == "score_0_5"
    assert result.metadata["model"]["model_id"] == "tcis-twostage-resnet50"


def test_comfort_emits_deprecation_and_keeps_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame(
        {
            "Filename": ["p1.jpg"],
            CANONICAL_SCORE: [3.2],
            "visual_comfort": [2.8],
        }
    )

    def fake_paths(*_args, **_kwargs):
        return frame.copy()

    monkeypatch.setattr(
        "urbancode.streetview.perception.predict_paths", fake_paths
    )
    with pytest.warns(DeprecationWarning, match="thermal_affordance"):
        out = uc.streetview.comfort("p1.jpg", mode="image", device="cpu")
    assert LEGACY_SCORE in out.columns
    assert out[LEGACY_SCORE].iloc[0] == 3.2
