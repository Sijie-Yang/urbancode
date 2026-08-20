"""Spectral indices computed by band name, never by array position."""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from urbancode.city import Layer
from urbancode.imagery.source import derived_layer, is_band_map, open_raster

BandMap = Mapping[str, np.ndarray]

RED_NAMES = ("red", "B04", "B4", "Red")
NIR_NAMES = ("nir", "B08", "B8", "NIR")
GREEN_NAMES = ("green", "B03", "B3", "Green")
SWIR_NAMES = ("swir", "swir16", "B11", "B12", "SWIR")


def band(bands: BandMap, *names: str) -> np.ndarray:
    """Return the first matching band as float64."""
    for name in names:
        if name in bands:
            return np.asarray(bands[name], dtype=float)
    raise KeyError(
        f"none of {names} found in bands {list(bands)}; "
        "indices require named bands, not positional arrays"
    )


def _ratio(numer: np.ndarray, denom: np.ndarray, nodata: float) -> np.ndarray:
    out = np.full(numer.shape, nodata, dtype=float)
    mask = denom != 0
    np.divide(numer, denom, out=out, where=mask)
    return out


def _ndvi_from_bands(bands: BandMap, nodata: float) -> np.ndarray:
    red = band(bands, *RED_NAMES)
    nir = band(bands, *NIR_NAMES)
    return _ratio(nir - red, nir + red, nodata)


def _ndwi_from_bands(bands: BandMap, nodata: float) -> np.ndarray:
    green = band(bands, *GREEN_NAMES)
    nir = band(bands, *NIR_NAMES)
    return _ratio(green - nir, green + nir, nodata)


def _ndbi_from_bands(bands: BandMap, nodata: float) -> np.ndarray:
    swir = band(bands, *SWIR_NAMES)
    nir = band(bands, *NIR_NAMES)
    return _ratio(swir - nir, swir + nir, nodata)


def ndvi(source: Any, nodata: float = np.nan) -> np.ndarray | Layer:
    """(NIR - Red) / (NIR + Red).

    A Layer, GeoTIFF path, or DataArray returns a :class:`~urbancode.city.Layer`.
    A name-to-array mapping returns a NumPy array.
    """
    if is_band_map(source):
        return _ndvi_from_bands(source, nodata)
    src = open_raster(source)
    return derived_layer(
        "ndvi",
        _ndvi_from_bands(src.bands, nodata),
        src,
        nodata=nodata,
        processing={"op": "ndvi"},
        extra={"unit": "dimensionless"},
    )


def ndwi(source: Any, nodata: float = np.nan) -> np.ndarray | Layer:
    """(Green - NIR) / (Green + NIR).

    A Layer, GeoTIFF path, or DataArray returns a :class:`~urbancode.city.Layer`.
    A name-to-array mapping returns a NumPy array.
    """
    if is_band_map(source):
        return _ndwi_from_bands(source, nodata)
    src = open_raster(source)
    return derived_layer(
        "ndwi",
        _ndwi_from_bands(src.bands, nodata),
        src,
        nodata=nodata,
        processing={"op": "ndwi"},
        extra={"unit": "dimensionless"},
    )


def ndbi(source: Any, nodata: float = np.nan) -> np.ndarray | Layer:
    """(SWIR - NIR) / (SWIR + NIR).

    A Layer, GeoTIFF path, or DataArray returns a :class:`~urbancode.city.Layer`.
    A name-to-array mapping returns a NumPy array.
    """
    if is_band_map(source):
        return _ndbi_from_bands(source, nodata)
    src = open_raster(source)
    return derived_layer(
        "ndbi",
        _ndbi_from_bands(src.bands, nodata),
        src,
        nodata=nodata,
        processing={"op": "ndbi"},
        extra={"unit": "dimensionless"},
    )
