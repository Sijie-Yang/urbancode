from __future__ import annotations

from examples.live.build_gs_catalog import FILTERS, _passes_filter


def test_tcis_filter_keeps_any_daytime_street_photo() -> None:
    assert _passes_filter({"lighting_condition": "day"})
    assert _passes_filter(
        {
            "lighting_condition": "daytime",
            "view_direction": "side",
            "quality": "poor",
            "glare": "yes",
            "pano_status": "yes",
            "projection_type": "spherical",
        }
    )
    assert "day" in FILTERS["lighting_condition"]
    assert set(FILTERS) == {"lighting_condition"}


def test_tcis_filter_drops_night() -> None:
    assert not _passes_filter({"lighting_condition": "night"})
    assert not _passes_filter({"lighting_condition": "dusk"})
    assert not _passes_filter({"lighting_condition": ""})
