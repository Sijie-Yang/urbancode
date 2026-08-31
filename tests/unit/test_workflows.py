from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2] / "examples" / "workflows"


def test_punggol_end_to_end(tmp_path: Path) -> None:
    pytest.importorskip("geopandas")
    pytest.importorskip("rasterio")
    pytest.importorskip("networkx")
    pytest.importorskip("matplotlib")
    from examples.workflows.punggol_end_to_end import main

    out = main(tmp_path)
    assert {"ndvi", "reachability"} <= set(out["table"]["indicator"])
    assert out["saved"] is not None
    assert (Path(out["saved"]) / "provenance" / "receipts.jsonl").exists()
    methods = {item.get("method") for item in out["receipts"]}
    assert "aggregate" in methods
    assert out["figures"]


def test_streetview_to_grid(tmp_path: Path) -> None:
    pytest.importorskip("geopandas")
    pytest.importorskip("cv2")
    pytest.importorskip("PIL")
    from examples.workflows.streetview_to_grid import main

    out = main(tmp_path)
    assert out["layer"].kind == "vector"
    color = float(out["features"]["Colorfulness"].iloc[0])
    assert color != 0.42
    assert out["features"]["location_quality"].iloc[0] == "illustrative"
    assert any(r.value is not None for r in out["result"].records)
    flags = [flag for rec in out["result"].records for flag in rec.quality_flags]
    assert "synthetic_location" in flags


def test_multi_city_contract() -> None:
    pytest.importorskip("geopandas")
    pytest.importorskip("rasterio")
    pytest.importorskip("networkx")
    from examples.workflows.multi_city_contract import main

    out = main()
    assert out["cities"] == ["helsinki", "nyc", "punggol"]
    assert set(out["indicators"]) == {"ndvi", "reachability"}


def test_green_accessibility(tmp_path: Path) -> None:
    pytest.importorskip("geopandas")
    pytest.importorskip("rasterio")
    pytest.importorskip("networkx")
    pytest.importorskip("matplotlib")
    from examples.workflows.green_accessibility import main

    out = main(tmp_path)
    assert {"ndvi", "park_near_m", "reachability"} <= set(out["result"].to_pandas()["indicator"])


def test_street_experience(tmp_path: Path) -> None:
    pytest.importorskip("geopandas")
    pytest.importorskip("cv2")
    pytest.importorskip("rasterio")
    from examples.workflows.street_experience import main

    out = main(tmp_path)
    assert {"colorfulness", "photo_count", "ndvi"} <= set(
        out["result"].to_pandas()["indicator"]
    )
    assert out["n"] >= 1


def test_real_heat_stress(tmp_path: Path) -> None:
    pytest.importorskip("geopandas")
    pytest.importorskip("rasterio")
    pytest.importorskip("pythermalcomfort")
    from examples.workflows.real_heat_stress import main

    out = main(tmp_path)
    assert out["layer"].name == "utci"
    flags = {flag for rec in out["result"].records for flag in rec.quality_flags}
    assert "modelled_mrt_proxy" in flags
    assert "weather_imagery_date_gap" in flags
    assert out["result"].metadata["date_gap_days"] == 13


def test_climate_heat_stress(tmp_path: Path) -> None:
    pytest.importorskip("geopandas")
    pytest.importorskip("rasterio")
    pytest.importorskip("pythermalcomfort")
    from examples.workflows.climate_heat_stress import main

    out = main(tmp_path)
    assert out["layer"].name == "utci"
    assert any(r.indicator == "utci" for r in out["result"].records)
