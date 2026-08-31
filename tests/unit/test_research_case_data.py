from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "examples" / "data" / "research_cases" / "thermal_comfort_in_sight"
STREETVIEW = ROOT / "examples" / "data" / "real" / "streetview"


def test_case_manifest_has_source_license_citation() -> None:
    manifest = json.loads((CASE / "manifest.json").read_text(encoding="utf-8"))
    for key in ("source", "license", "citation", "checksums", "n_images"):
        assert manifest.get(key), key
    assert "not a Punggol census" in manifest["sample_warning"]
    assert (CASE / "LICENSE.md").is_file()
    assert "placeholder" not in (CASE / "LICENSE.md").read_text().lower()
    assert "synthetic" not in manifest["source"]


def test_case_photos_are_licensed_commons_files() -> None:
    catalog = json.loads((STREETVIEW / "catalog.json").read_text(encoding="utf-8"))
    punggol = [row for row in catalog if row.get("city_id") == "punggol"]
    assert len(punggol) == 8
    for row in punggol:
        path = STREETVIEW / row["path"]
        assert path.is_file(), path
        assert row["source"] == "wikimedia-commons"
        assert "CC" in row["license"]
        assert row.get("checksum")
        assert row.get("latitude") and row.get("longitude")


def test_predictions_if_present_are_real_tcis_columns() -> None:
    path = CASE / "predictions.csv"
    if not path.is_file():
        return
    frame = pd.read_csv(path)
    assert "image_id" in frame.columns
    assert "thermal_affordance" in frame.columns
    assert "synthetic" not in path.read_text().lower()
    assert frame["thermal_affordance"].notna().any()
    assert not (frame["thermal_affordance"] == 0).all()
