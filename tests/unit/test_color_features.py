from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("torch")
pytest.importorskip("PIL")

from urbancode.streetview.features import COLOR_FEATURE_NAMES, color


def test_color_corrupt_image_returns_nan(tmp_path: Path) -> None:
    bad = tmp_path / "broken.jpg"
    bad.write_bytes(b"not-an-image")
    frame = pd.DataFrame({"Filename": [bad.name]})
    out = color(frame, folder_path=str(tmp_path))
    for name in COLOR_FEATURE_NAMES:
        assert name in out.columns
        assert pd.isna(out[name].iloc[0])
