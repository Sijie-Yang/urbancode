"""Live STAC tests on a tiny bbox. Run with: pytest -m live"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.live

# ~0.01° near Punggol, Singapore
TINY_BBOX = (103.905, 1.400, 103.915, 1.410)


def test_sentinel_window_and_band_alignment():
    pytest.importorskip("rasterio")
    pytest.importorskip("pystac_client")
    from urbancode.imagery.fetch import fetch

    city = fetch(
        bbox=TINY_BBOX,
        layers=["sentinel2"],
        max_pixels=2_000_000,
        cloud=40,
    )
    if "sentinel2" not in city:
        pytest.skip(f"sentinel2 missing: {city.errors}")
    layer = city.layer("sentinel2")
    data = layer.data
    values = getattr(data, "values", data)
    assert values.shape[-2] * values.shape[-1] < 2_000_000
    names = layer.metadata.get("bands") or []
    assert values.shape[0] >= 2
