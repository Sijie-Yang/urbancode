from __future__ import annotations

import json
from pathlib import Path

import pytest

from examples.live.build_singapore_svi_catalog import build_catalog, main

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "examples" / "data" / "research_cases" / "thermal_comfort_in_sight_singapore"


def test_singapore_manifest_says_raw_imagery_unavailable() -> None:
    manifest = json.loads((CASE / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["raw_imagery"] == "unavailable"
    assert manifest["n_images_expected"] == 92233
    assert manifest["predictions"] == "full_92233_complete"
    assert manifest["full_92233"]["host"] == "ual-chark"
    assert "5090" in manifest["full_92233"]["gpu"]
    assert manifest["full_92233"]["success"] == 92233
    assert manifest["full_92233"]["failed"] == 0
    assert manifest["stage_1000"]["host"] == "Alienware"
    assert "3070 Ti" in manifest["stage_1000"]["gpu"]
    assert "not the flagship" in manifest["tiny_fixture_note"]
    assert (CASE / "LICENSE.md").is_file()
    assert "not assumed redistributable" in (CASE / "LICENSE.md").read_text().lower() or (
        "not" in (CASE / "LICENSE.md").read_text().lower()
        and "redistribut" in (CASE / "LICENSE.md").read_text().lower()
    )
    assert (CASE / "predictions_receipt.json").is_file()
    assert (CASE / "predictions_checksum.json").is_file()
    checksum = json.loads((CASE / "predictions_checksum.json").read_text(encoding="utf-8"))
    assert checksum["n_rows"] == 92233
    assert checksum["predictions_sha256"] == manifest["predictions_sha256"]
    assert checksum["not_in_git"] is True


def test_catalog_builder_parses_id_lon_lat(tmp_path: Path) -> None:
    (tmp_path / "10000_103.851580191128_1.43035816001434.jpg").write_bytes(b"x")
    (tmp_path / "9_103.942088295571_1.33926551633721.jpg").write_bytes(b"x")
    catalog = build_catalog(tmp_path)
    assert len(catalog) == 2
    assert set(catalog["image_id"]) == {"10000", "9"}
    assert catalog.loc[catalog["image_id"] == "10000", "longitude"].iloc[0] == 103.851580191128
    pytest.importorskip("pyarrow")
    summary = main(
        [
            "--image-root",
            str(tmp_path),
            "--output",
            str(tmp_path / "out" / "tcis_svi_catalog.parquet"),
        ]
    )
    assert summary["n_images"] == 2
    assert summary["n_geolocated"] == 2
    assert "D:" not in json.dumps(summary)
    assert (tmp_path / "out" / "catalog_summary.json").is_file()
