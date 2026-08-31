from __future__ import annotations

from pathlib import Path

import pytest

from examples.tutorials.quickstart import EXPECTED, PUNGGOL, run

DOCS = Path(__file__).resolve().parents[2] / "docs" / "source"


def test_quickstart_numbers_match_docs() -> None:
    pytest.importorskip("geopandas")
    pytest.importorskip("rasterio")
    pytest.importorskip("networkx")
    assert PUNGGOL.is_dir()
    out = run()
    assert out["n_cells"] == EXPECTED["n_cells"]
    assert out["ndvi_mean"] == pytest.approx(EXPECTED["ndvi_mean"], abs=0.001)
    assert out["reach_nulls"] == EXPECTED["reach_nulls"]
    assert out["n_nodes"] == EXPECTED["n_nodes"]


def test_quickstart_docs_include_the_script() -> None:
    text = (DOCS / "getting_started" / "quickstart.rst").read_text(encoding="utf-8")
    assert "examples/tutorials/quickstart.py" in text
    assert "81" in text
    assert "0.208" in text
    assert "1425" in text
