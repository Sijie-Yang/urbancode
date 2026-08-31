from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "examples" / "data" / "research_cases" / "heat_resilience_in_sight"
SCRIPT = ROOT / "examples" / "research_cases" / "heat_resilience_in_sight.py"
DOCS = ROOT / "docs" / "source" / "workflows" / "research_cases" / "heat_resilience_in_sight.rst"


def test_hris_singapore_panel_is_not_tcis_92233() -> None:
    manifest = json.loads((CASE / "manifest.json").read_text(encoding="utf-8"))
    stats = pd.read_csv(CASE / "city_vata_stats.csv")
    calibration = json.loads((CASE / "calibration.json").read_text(encoding="utf-8"))
    sg_n = int(stats.loc[stats["city"] == "svi_sg", "n"].iloc[0])
    assert sg_n == 21772
    assert manifest["singapore_hris_n"] == 21772
    assert manifest["singapore_tcis_n"] == 92233
    assert round(float(calibration["d_ref"]), 3) == 7.991
    assert round(float(calibration["v_ref"]), 3) == 1.732
    assert calibration["cache_version"] == "hourly_v1"
    assert calibration["calibrate_city"] == "svi_hk"
    copy = " ".join(
        [
            manifest["role"],
            manifest["singapore_note"],
            SCRIPT.read_text(encoding="utf-8"),
            DOCS.read_text(encoding="utf-8"),
        ]
    ).lower()
    assert "application" in copy
    assert "not a validation" in copy
    assert "21,772" in manifest["singapore_note"] or "21772" in copy
    assert "92,233" in manifest["singapore_note"]
    assert (CASE / "LICENSE.md").is_file()
    assert (CASE / "checksums.sha256").is_file()
    assert "johannesburg" in (CASE / "LICENSE.md").read_text().lower()
