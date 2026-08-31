from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from urbancode.streetview.contract import (
    ContractError,
    initial_feature_names,
    initial_features_from_frame,
    load_feature_stats,
    load_manifest,
    missing_initial_features,
    normalize_initial_features,
    output_feature_names,
    validate_state_dict,
)
from urbancode.streetview.weights import BUNDLED_STATS, ensure_tcis_artifacts


def test_manifest_locks_feature_counts() -> None:
    manifest = load_manifest()
    assert manifest["model_version"] == "tcis-code4"
    assert len(initial_feature_names()) == 59
    assert len(manifest["head_feature_names"]) == 20
    assert output_feature_names()[0] == "thermal_comfort"
    assert output_feature_names()[1] == "visual_comfort"
    assert manifest["head_feature_names"][0] == "comfort"
    assert manifest["output_name_map"]["comfort"] == "visual_comfort"


def test_select_features_by_name_not_position() -> None:
    names = initial_feature_names()
    extra = pd.DataFrame(
        {
            "Filename": ["a.jpg"],
            "noise": [99.0],
            **{name: [float(i)] for i, name in enumerate(names)},
        }
    )
    # Insert a column that would shift iloc[22:81].
    extra.insert(1, "thermal_comfort", 0.0)
    values = initial_features_from_frame(extra)
    assert values.shape == (1, 59)
    assert values[0, 0] == 0.0
    assert values[0, 1] == 1.0


def test_missing_feature_raises() -> None:
    names = initial_feature_names()
    frame = pd.DataFrame({name: [0.0] for name in names[:-1]})
    missing = missing_initial_features(frame.columns)
    assert missing == [names[-1]]
    with pytest.raises(ContractError, match="missing TCIS initial features"):
        initial_features_from_frame(frame)


def test_wrong_stats_length(tmp_path: Path) -> None:
    path = tmp_path / "feature_stats.npz"
    np.savez(path, mins=np.zeros(10), maxs=np.ones(10))
    with pytest.raises(ContractError, match="length mismatch"):
        load_feature_stats(path, n_features=59)


def test_bundled_stats_match_contract() -> None:
    mins, maxs = load_feature_stats(BUNDLED_STATS, n_features=59)
    assert mins.shape == (59,)
    assert maxs.shape == (59,)
    normalized = normalize_initial_features(mins, mins, maxs)
    assert np.allclose(normalized, 0.0)


def test_wrong_weights_rejected() -> None:
    class _T:
        def __init__(self, shape: tuple[int, ...]) -> None:
            self.shape = shape

    bad = {
        "task_layers.0.weight": _T((1024, 100)),
        "task_layers.9.weight": _T((20, 256)),
        "final_layer.0.weight": _T((512, 2127)),
        "final_layer.6.weight": _T((1, 256)),
    }
    with pytest.raises(ContractError, match="task_layers input dim"):
        validate_state_dict(bad)

    missing = {"task_layers.0.weight": _T((1024, 2107))}
    with pytest.raises(ContractError, match="missing keys"):
        validate_state_dict(missing)


def test_valid_state_dict_shapes() -> None:
    class _T:
        def __init__(self, shape: tuple[int, ...]) -> None:
            self.shape = shape

    ok = {
        "task_layers.0.weight": _T((1024, 2107)),
        "task_layers.9.weight": _T((20, 256)),
        "final_layer.0.weight": _T((512, 2127)),
        "final_layer.6.weight": _T((1, 256)),
    }
    validate_state_dict(ok)


def _accept_manifest_sha(monkeypatch: pytest.MonkeyPatch) -> None:
    from urbancode.streetview import weights as weights_mod

    manifest = load_manifest()

    def fake_sha(path: Path) -> str:
        name = Path(path).name
        if ".npz" in name or "feature_stats" in name:
            return str(manifest["stats_sha256"])
        return str(manifest["weights_sha256"])

    monkeypatch.setattr(weights_mod, "_sha256", fake_sha)


def test_ensure_weights_cache_hit(
    cache_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from urbancode.cache import models_dir

    _accept_manifest_sha(monkeypatch)
    dest = models_dir()
    weights = dest / "best_model.pth"
    stats = dest / "feature_stats.npz"
    weights.write_bytes(b"fake-weights")
    stats.write_bytes(BUNDLED_STATS.read_bytes())

    def _fail(*_args, **_kwargs):
        raise AssertionError("download should not run on cache hit")

    with patch("urbancode.streetview.weights._hf_download", _fail):
        got_w, got_s = ensure_tcis_artifacts()
    assert got_w == weights
    assert got_s == stats


def test_ensure_weights_dataset_then_fallback(
    cache_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from urbancode.cache import models_dir

    _accept_manifest_sha(monkeypatch)
    calls: list[tuple[str, str]] = []

    def fake_download(
        repo_id: str, filename: str, *, repo_type: str, revision: str = "main"
    ) -> Path:
        calls.append((repo_id, filename))
        if repo_id.endswith("Dataset") and filename.endswith(".pth"):
            raise RuntimeError("dataset missing weights")
        out = cache_dir / filename.replace("/", "_")
        out.parent.mkdir(parents=True, exist_ok=True)
        if filename.endswith(".npz"):
            out.write_bytes(BUNDLED_STATS.read_bytes())
        else:
            out.write_bytes(b"weights")
        return out

    with patch("urbancode.streetview.weights._hf_download", fake_download):
        weights, stats = ensure_tcis_artifacts()

    assert (models_dir() / "best_model.pth").exists()
    assert weights.exists()
    assert stats.exists()
    assert any(item[0].endswith("Thermal-Affordance-Model") for item in calls)


def test_ensure_weights_preserves_download_error(cache_dir: Path) -> None:
    def fake_download(*_args, **_kwargs):
        raise RuntimeError("network down")

    with patch("urbancode.streetview.weights._hf_download", fake_download):
        with pytest.raises(FileNotFoundError, match="network down"):
            ensure_tcis_artifacts()
