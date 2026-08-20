from __future__ import annotations

from pathlib import Path

import pytest

from .helpers import load_offline
from .png_checks import assert_gallery_png

pytestmark = pytest.mark.gallery_streetview


def test_streetview_results_does_not_call_comfort(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("PIL")
    pytest.importorskip("matplotlib")

    def _boom(*_args, **_kwargs):
        raise AssertionError("offline streetview gallery must not call comfort()")

    monkeypatch.setattr("urbancode.streetview.comfort", _boom, raising=False)
    result = load_offline("07_streetview_results.py").main(tmp_path, add_basemap=False)
    assert_gallery_png(result["figure"])
