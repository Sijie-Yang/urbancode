from __future__ import annotations

import numpy as np
import pytest

from urbancode.imagery.indices import ndbi, ndvi, ndwi
from urbancode.imagery.terrain import aspect_degrees, hillshade, slope_degrees


def test_ndvi_by_band_name_not_position() -> None:
    red = np.array([[1.0, 2.0], [3.0, 4.0]])
    nir = np.array([[3.0, 2.0], [1.0, 6.0]])
    # Deliberately put NIR first in the dict so positional code would fail.
    bands = {"nir": nir, "red": red, "noise": np.ones((2, 2))}
    out = ndvi(bands)
    expected = (nir - red) / (nir + red)
    assert np.allclose(out, expected)


def test_ndvi_zero_denominator_is_nodata() -> None:
    bands = {
        "B04": np.array([[0.0]]),
        "B08": np.array([[0.0]]),
    }
    out = ndvi(bands, nodata=-9999)
    assert out[0, 0] == -9999


def test_ndwi_and_ndbi_require_named_bands() -> None:
    with pytest.raises(KeyError, match="named bands"):
        ndwi({"foo": np.ones((1, 1))})
    green = np.array([[2.0]])
    nir = np.array([[1.0]])
    swir = np.array([[3.0]])
    assert ndwi({"green": green, "nir": nir})[0, 0] == pytest.approx(1 / 3)
    assert ndbi({"B11": swir, "B08": nir})[0, 0] == pytest.approx(0.5)


def test_slope_aspect_hillshade() -> None:
    dem = np.array([[0.0, 0.0], [10.0, 10.0]])
    sl = slope_degrees(dem, resolution=10.0)
    assert sl.shape == (2, 2)
    assert np.all(sl >= 0)
    asp = aspect_degrees(dem, resolution=10.0)
    assert asp.min() >= 0
    hs = hillshade(dem, resolution=10.0)
    assert hs.min() >= 0
    assert hs.max() <= 255
    with pytest.raises(ValueError):
        slope_degrees(dem, 0)
