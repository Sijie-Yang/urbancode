from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

gpd = pytest.importorskip("geopandas")

import urbancode as uc


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "image_id": ["a", "b"],
            "image_path": ["photos/a.jpg", "photos/b.jpg"],
            "longitude": [103.91, 103.912],
            "latitude": [1.406, 1.407],
            "source": ["wikimedia-commons", "wikimedia-commons"],
            "license": ["CC BY-SA 4.0", "CC BY-SA 4.0"],
        }
    )


def test_from_table_requires_unique_image_id() -> None:
    frame = _frame()
    frame.loc[1, "image_id"] = "a"
    with pytest.raises(ValueError, match="unique"):
        uc.images.from_table(frame, view_type="streetview")


def test_from_table_requires_explicit_id() -> None:
    frame = _frame().drop(columns=["image_id"])
    with pytest.raises(ValueError, match="image_id"):
        uc.images.from_table(frame, view_type="streetview")


def test_from_table_uri_hash_strategy() -> None:
    frame = _frame().drop(columns=["image_id"])
    layer = uc.images.from_table(
        frame, id_column=None, view_type="streetview", id_strategy="uri_hash"
    )
    ids = list(layer.data["image_id"])
    assert len(ids) == 2
    assert ids[0] != ids[1]
    expected = "img:" + hashlib.sha256(b"photos/a.jpg").hexdigest()[:16]
    assert ids[0] == expected
    assert layer.metadata["id_strategy"] == "uri_hash"


def test_from_table_schema_and_crs() -> None:
    layer = uc.images.from_table(
        _frame(),
        view_type="streetview",
        city_id="punggol",
        source="wikimedia-commons",
        license="CC BY-SA 4.0",
    )
    assert isinstance(layer, uc.Layer)
    assert layer.kind == "vector"
    assert str(layer.crs) in {"EPSG:4326", "epsg:4326"}
    cols = set(layer.data.columns)
    for name in (
        "image_id",
        "image_path",
        "view_type",
        "city_id",
        "source",
        "license",
        "captured_at",
        "location_quality",
    ):
        assert name in cols
    assert set(layer.data["view_type"]) == {"streetview"}
    assert layer.metadata["view_type"] == "streetview"


def test_from_table_rejects_unknown_view_type() -> None:
    with pytest.raises(ValueError, match="view_type"):
        uc.images.from_table(_frame(), view_type="satellite")


def test_from_table_without_coords_is_table_layer() -> None:
    frame = _frame().drop(columns=["longitude", "latitude"])
    layer = uc.images.from_table(frame, view_type="windowview")
    assert layer.kind == "table"
    assert set(layer.data["view_type"]) == {"windowview"}


def test_from_table_reads_json_catalog(tmp_path) -> None:
    catalog = tmp_path / "catalog.json"
    catalog.write_text(
        '[{"image_id":"a","path":"a.jpg","longitude":103.91,"latitude":1.406}]',
        encoding="utf-8",
    )
    layer = uc.images.from_table(catalog, view_type="streetview")
    assert layer.metadata["n_images"] == 1
    assert Path(layer.data["image_path"].iloc[0]) == tmp_path / "a.jpg"


def test_from_table_image_root_resolves_relative_paths(tmp_path) -> None:
    frame = _frame()
    frame["relative_path"] = ["a.jpg", "b.jpg"]
    frame = frame.drop(columns=["image_path"])
    layer = uc.images.from_table(
        frame,
        path_column="relative_path",
        view_type="streetview",
        image_root=tmp_path,
        source=frame["source"],
    )
    assert list(layer.data["relative_path"]) == ["a.jpg", "b.jpg"]
    assert Path(layer.data["image_path"].iloc[0]) == tmp_path / "a.jpg"
    assert layer.metadata["image_root_provided"] is True
    assert "image_root" not in layer.metadata


def test_streetview_as_layer_reads_json_catalog(tmp_path) -> None:
    catalog = tmp_path / "catalog.json"
    catalog.write_text(
        '[{"image_id":"a","path":"a.jpg","longitude":103.91,"latitude":1.406}]',
        encoding="utf-8",
    )
    points = uc.streetview.as_layer(catalog)
    assert points.source == "urbancode.streetview.as_layer"
    assert points.metadata["n_images"] == 1


def test_streetview_as_layer_wraps_images_contract() -> None:
    points = uc.streetview.as_layer(_frame(), name="streetview_points")
    assert points.source == "urbancode.streetview.as_layer"
    assert points.metadata["view_type"] == "streetview"
    assert points.metadata["processing"]["wrapped"] == "urbancode.images.from_table"
    assert "image_id" in points.data.columns
    assert set(points.data["view_type"]) == {"streetview"}
