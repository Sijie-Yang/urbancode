from __future__ import annotations

import math
from pathlib import Path

import pytest

from urbancode.indicators import IndicatorRecord, IndicatorResult
from urbancode.provenance import FLAG_NODATA, is_missing, quality_flags


def test_missing_is_not_zero() -> None:
    rec = IndicatorRecord(
        city_id="punggol",
        unit_id="grid:250:0:0",
        indicator="ndvi",
        value=None,
        coverage=0.0,
    )
    assert rec.value is None
    assert FLAG_NODATA in rec.quality_flags
    assert rec.value != 0
    assert is_missing(float("nan"))
    assert 0 not in quality_flags(value=None)


def test_roundtrip_csv(tmp_path: Path) -> None:
    result = IndicatorResult(
        records=[
            IndicatorRecord(
                city_id="punggol",
                unit_id="grid:250:0:0",
                indicator="ndvi",
                value=0.42,
                unit="1",
                method="zonal_stats",
                parameters={"stat": "mean"},
                coverage=1.0,
            ),
            IndicatorRecord(
                city_id="punggol",
                unit_id="grid:250:0:1",
                indicator="ndvi",
                value=None,
                coverage=0.0,
            ),
        ],
        metadata={"op": "test"},
    )
    out = result.save(tmp_path / "result")
    assert (out / "provenance" / "receipts.jsonl").exists()
    loaded = IndicatorResult.load(out)
    assert len(loaded.records) == 2
    assert loaded.records[0].value == pytest.approx(0.42)
    assert loaded.records[1].value is None
    assert loaded.records[1].value != 0
    table = loaded.to_pandas()
    assert math.isnan(float(table.loc[table["unit_id"] == "grid:250:0:1", "value"].iloc[0]))
    assert isinstance(table.loc[0, "parameters"], dict)
    layer = loaded.to_layer()
    assert layer.kind == "table"


def test_multi_indicator_requires_name() -> None:
    result = IndicatorResult(
        records=[
            IndicatorRecord("a", "u1", "ndvi", 0.2),
            IndicatorRecord("a", "u1", "reachability", 3.0),
        ]
    )
    with pytest.raises(ValueError, match="indicator="):
        result.to_layer()
    layer = result.to_layer(indicator="ndvi")
    assert layer.name == "ndvi"
    assert list(layer.data["indicator"].unique()) == ["ndvi"]


def test_coverage_out_of_range_raises() -> None:
    with pytest.raises(ValueError, match="coverage"):
        IndicatorRecord("a", "u1", "ndvi", 0.2, coverage=1.5)


def test_duplicate_keep_preserves_both_rows() -> None:
    result = IndicatorResult(
        records=[
            IndicatorRecord("a", "u1", "ndvi", 0.2),
            IndicatorRecord("a", "u1", "ndvi", 0.3),
        ],
        on_duplicate="keep",
    )
    assert len(result.records) == 2
    assert [rec.value for rec in result.records] == [0.2, 0.3]


def test_on_duplicate_rejects_unknown_policy() -> None:
    with pytest.raises(ValueError, match="unsupported on_duplicate"):
        IndicatorResult(
            records=[IndicatorRecord("a", "u1", "ndvi", 0.2)],
            on_duplicate="last",
        )


def test_roundtrip_restores_units_metadata(tmp_path: Path) -> None:
    pytest.importorskip("geopandas")
    from urbancode.units import AnalysisUnits

    gpd = pytest.importorskip("geopandas")
    from shapely.geometry import box

    frame = gpd.GeoDataFrame(
        {"unit_id": ["u1"], "geometry": [box(0, 0, 1, 1)]},
        crs="EPSG:32648",
    )
    units = AnalysisUnits(
        frame=frame,
        city_id="punggol",
        kind="grid",
        cell_size=250,
        crs="EPSG:32648",
        metric_crs="EPSG:32648",
        metadata={"scheme": "world-origin", "note": "roundtrip"},
    )
    result = IndicatorResult(
        records=[IndicatorRecord("punggol", "u1", "ndvi", 0.2, coverage=1.0)],
        units=units,
        metadata={"op": "test"},
    )
    loaded = IndicatorResult.load(result.save(tmp_path / "result"))
    assert loaded.units is not None
    assert loaded.units.metadata["scheme"] == "world-origin"
    assert loaded.units.metadata["note"] == "roundtrip"


def test_duplicate_keys_raise() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        IndicatorResult(
            records=[
                IndicatorRecord("a", "u1", "ndvi", 0.2),
                IndicatorRecord("a", "u1", "ndvi", 0.3),
            ]
        )


def test_to_xarray_empty_time() -> None:
    try:
        import xarray as xr
    except Exception:
        pytest.skip("xarray is not importable")
    result = IndicatorResult(
        records=[
            IndicatorRecord("a", "u1", "ndvi", 0.2),
            IndicatorRecord("a", "u2", "ndvi", 0.3),
        ]
    )
    dataset = result.to_xarray()
    assert "unit_id" in dataset.coords or "unit_id" in dataset.dims
    del xr
