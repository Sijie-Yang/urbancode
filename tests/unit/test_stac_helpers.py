from __future__ import annotations

from datetime import datetime, timezone

from types import SimpleNamespace

from urbancode.imagery.stac import (
    DEFAULT_CLOUD,
    SCL_CLOUD,
    covering_date_items,
    default_time_range,
    items_cover_bbox,
)


def test_default_time_range_is_last_12_months() -> None:
    interval = default_time_range()
    start, end = interval.split("/")
    start_d = datetime.fromisoformat(start).date()
    end_d = datetime.fromisoformat(end).date()
    today = datetime.now(timezone.utc).date()
    assert end_d == today
    assert 360 <= (end_d - start_d).days <= 366


def test_scl_and_cloud_defaults() -> None:
    assert DEFAULT_CLOUD == 20
    assert 3 in SCL_CLOUD
    assert 4 not in SCL_CLOUD
    assert {8, 9, 10} <= SCL_CLOUD


def test_covering_date_prefers_full_aoi() -> None:
    bbox = (103.9, 1.40, 103.92, 1.42)
    partial = SimpleNamespace(
        id="a",
        bbox=(103.9, 1.40, 103.905, 1.41),
        properties={"datetime": "2025-01-01T00:00:00Z", "eo:cloud_cover": 1},
    )
    full_a = SimpleNamespace(
        id="b",
        bbox=(103.89, 1.39, 103.93, 1.43),
        properties={"datetime": "2025-01-02T00:00:00Z", "eo:cloud_cover": 5},
    )
    assert not items_cover_bbox([partial], bbox)
    assert items_cover_bbox([full_a], bbox)
    chosen = covering_date_items([partial, full_a], bbox)
    assert [it.id for it in chosen] == ["b"]
