from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from urbancode.area import StudyArea
from urbancode.city import City, load
from urbancode.provenance import ProvenanceRecord, stamp_layer


def test_provenance_receipts_roundtrip(tmp_path: Path) -> None:
    rec = ProvenanceRecord(source="osm", method="fetch", crs="EPSG:4326")
    city = City(place="T")
    city.metadata["provenance"] = [rec.to_record()]
    city.add_layer("scores", pd.DataFrame({"v": [1]}), kind="table")
    out = city.to_dir(tmp_path / "city")
    assert (out / "provenance" / "receipts.jsonl").exists()
    loaded = load(out)
    assert loaded.metadata["provenance"][0]["provenance_id"] == rec.provenance_id
    assert loaded.metadata["provenance"][0]["method"] == "fetch"


def test_stamp_layer_sets_id() -> None:
    city = City(place="T")
    layer = city.add_layer(
        "scores",
        pd.DataFrame({"v": [1]}),
        kind="table",
        metadata={"processing": {"op": "table"}},
    )
    stamped = stamp_layer(layer)
    assert layer.metadata["provenance_id"] == stamped.provenance_id
    assert layer.metadata["provenance"]["method"] == "table"


def test_study_area_persists(tmp_path: Path) -> None:
    pytest.importorskip("geopandas")
    pytest.importorskip("shapely")
    area = StudyArea.from_bbox(103.905, 1.4, 103.915, 1.41, place="Punggol, Singapore")
    city = City(area)
    city.add_layer("scores", pd.DataFrame({"v": [1]}), kind="table")
    out = city.to_dir(tmp_path / "city")
    assert (out / "area" / "study_area.gpkg").exists()
    loaded = load(out)
    assert loaded.study_area is not None
    assert loaded.study_area.bbox == area.bbox
    assert loaded.study_area.city_id == "punggol-singapore"
    assert loaded.study_area.projected_crs == area.metric_crs
