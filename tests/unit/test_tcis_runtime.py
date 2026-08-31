from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from urbancode.streetview.contract import load_feature_models_manifest, load_manifest


def test_feature_models_are_pinned() -> None:
    features = load_feature_models_manifest()
    seg = features["segformer"]
    assert seg["model"] == seg["processor"]
    assert len(seg["revision"]) == 40
    assert "ade-512-512" not in seg["processor"]
    assert features["faster_rcnn"]["weights"] == "COCO_V1"
    assert features["faster_rcnn"]["score_threshold"] == 0.0
    assert len(features["places365"]["weights_sha256"]) == 64
    assert len(features["places365"]["labels_sha256"]) == 64
    tcis = load_manifest()
    assert len(tcis["revision"]) == 40
    assert len(tcis["weights_sha256"]) == 64


def test_run_dataset_resumes_completed_ids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("pyarrow")
    from urbancode.perception.backends import tcis_runtime

    dest = tmp_path / "preds.parquet"
    pd.DataFrame(
        {
            "image_id": ["a"],
            "thermal_affordance": [3.1],
            "relative_path": ["a.jpg"],
        }
    ).to_parquet(dest, index=False)

    def fail_init(*_args, **_kwargs):
        raise AssertionError("TCISChain should not load when every image_id is done")

    monkeypatch.setattr(tcis_runtime, "TCISChain", fail_init)
    frame = pd.DataFrame(
        {
            "image_id": ["a"],
            "relative_path": ["a.jpg"],
            "longitude": [103.9],
            "latitude": [1.4],
        }
    )
    out = tcis_runtime.run_dataset(frame, output=dest, resume=True, device="cpu")
    assert list(out["image_id"]) == ["a"]
    assert out.attrs["tcis_provenance"]["skipped"] == 1


def test_export_frame_drops_absolute_paths() -> None:
    from urbancode.perception.backends.tcis_runtime import _export_frame

    frame = pd.DataFrame(
        {
            "image_id": ["a"],
            "image_path": [r"D:\svi\a.jpg"],
            "relative_path": ["a.jpg"],
            "thermal_affordance": [2.2],
        }
    )
    exported = _export_frame(frame)
    assert "image_path" not in exported.columns
    assert list(exported["relative_path"]) == ["a.jpg"]
