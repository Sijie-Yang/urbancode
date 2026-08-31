"""DEM derivatives computed from a 2-D elevation array."""

from __future__ import annotations

from typing import Any

import numpy as np

from urbancode.city import Layer
from urbancode.imagery.source import (
    derived_layer,
    is_numeric_array,
    open_raster,
)


def slope_degrees(dem: np.ndarray, resolution: float) -> np.ndarray:
    """Slope in degrees from a DEM and its ground resolution (metres)."""
    if resolution <= 0:
        raise ValueError("resolution must be positive")
    dy, dx = np.gradient(np.asarray(dem, dtype=float), resolution, resolution)
    return np.degrees(np.arctan(np.hypot(dx, dy)))


def aspect_degrees(dem: np.ndarray, resolution: float) -> np.ndarray:
    """Aspect in degrees clockwise from north (array API, no CRS checks)."""
    if resolution <= 0:
        raise ValueError("resolution must be positive")
    return _aspect_array(dem, resolution, resolution, nodata=None, flat_eps=0.0)


def _aspect_array(
    dem: np.ndarray,
    resolution_x: float,
    resolution_y: float,
    *,
    nodata: float | None,
    flat_eps: float,
) -> np.ndarray:
    if resolution_x <= 0 or resolution_y <= 0:
        raise ValueError("resolution must be positive")
    values = np.asarray(dem, dtype=float)
    invalid = ~np.isfinite(values)
    if nodata is not None and not (isinstance(nodata, float) and np.isnan(nodata)):
        invalid = invalid | (values == nodata)
    filled = np.where(invalid, np.nan, values)
    # axis 0 = southward rows on a north-up GeoTIFF; axis 1 = eastward columns
    d_south, d_east = np.gradient(filled, resolution_y, resolution_x)
    slope_mag = np.hypot(d_east, d_south)
    # downhill, degrees clockwise from north: atan2(east, north)
    downhill_east = -d_east
    downhill_north = d_south
    aspect = np.degrees(np.arctan2(downhill_east, downhill_north))
    aspect = np.mod(aspect, 360.0)
    if flat_eps > 0:
        aspect = np.where(slope_mag <= flat_eps, np.nan, aspect)
    aspect = np.where(invalid, np.nan, aspect)
    return aspect


def _is_geographic_crs(crs: Any) -> bool:
    if crs is None:
        return False
    if hasattr(crs, "is_geographic"):
        return bool(crs.is_geographic)
    text = str(crs).upper().replace(" ", "")
    return (
        "EPSG:4326" in text
        or text in {"4326", "OGC:CRS84", "CRS84"}
        or "GEOGCS" in text
    )


def _require_projected_crs(crs: Any) -> None:
    if crs is None:
        raise ValueError(
            "aspect() needs a projected CRS in metres. "
            "The DEM has no CRS; reproject it before calling aspect."
        )
    if _is_geographic_crs(crs):
        raise ValueError(
            "aspect() cannot use a geographic CRS (degrees are not metres). "
            "Reproject the DEM to a metric CRS such as UTM, then call aspect()."
        )


def _hillshade_array(
    dem: np.ndarray,
    resolution: float,
    azimuth: float = 315.0,
    altitude: float = 45.0,
) -> np.ndarray:
    sl = np.radians(slope_degrees(dem, resolution))
    asp = np.radians(aspect_degrees(dem, resolution))
    az = np.radians(azimuth)
    alt = np.radians(altitude)
    shaded = np.sin(alt) * np.cos(sl) + np.cos(alt) * np.sin(sl) * np.cos(az - asp)
    return np.clip(shaded * 255.0, 0, 255)


def slope(dem: Any, resolution: float | None = None) -> np.ndarray | Layer:
    """Slope in degrees.

    ``slope(layer_or_path)`` returns a :class:`~urbancode.city.Layer`.
    ``slope_degrees(array, resolution)`` is the array API.
    """
    if is_numeric_array(dem):
        if resolution is None:
            raise TypeError(
                "slope() on a NumPy array needs resolution in metres; "
                "pass a DEM Layer or GeoTIFF path, or call "
                "slope_degrees(array, resolution)."
            )
        return slope_degrees(dem, resolution)
    src = open_raster(dem)
    return derived_layer(
        "slope",
        slope_degrees(src.array_2d, src.resolution),
        src,
        processing={"op": "slope"},
    )


def aspect(dem: Any, resolution: float | None = None) -> np.ndarray | Layer:
    """Aspect in degrees clockwise from north.

    ``aspect(layer_or_path)`` returns a :class:`~urbancode.city.Layer`.
    Flat cells and nodata are ``nan``. Geographic CRS is rejected.
    ``aspect_degrees(array, resolution)`` is the array API.
    """
    if is_numeric_array(dem):
        if resolution is None:
            raise TypeError(
                "aspect() on a NumPy array needs resolution in metres; "
                "pass a DEM Layer or GeoTIFF path, or call "
                "aspect_degrees(array, resolution)."
            )
        return aspect_degrees(dem, resolution)
    src = open_raster(dem)
    _require_projected_crs(src.crs)
    res_x, res_y = src.resolution_xy
    array = _aspect_array(
        src.array_2d,
        res_x,
        res_y,
        nodata=src.nodata,
        flat_eps=1e-9,
    )
    return derived_layer(
        "aspect",
        array,
        src,
        nodata=float("nan"),
        processing={
            "op": "aspect",
            "convention": "degrees_clockwise_from_north",
            "flat": "nodata",
        },
        extra={"unit": "degree", "convention": "degrees_clockwise_from_north"},
    )


def hillshade(
    dem: Any,
    resolution: float | None = None,
    azimuth: float = 315.0,
    altitude: float = 45.0,
) -> np.ndarray | Layer:
    """Simple Lambertian hillshade, 0–255.

    ``hillshade(layer_or_path)`` returns a :class:`~urbancode.city.Layer`.
    ``hillshade(array, resolution)`` still returns a NumPy array.
    """
    if is_numeric_array(dem):
        if resolution is None:
            raise TypeError(
                "hillshade() on a NumPy array needs resolution in metres; "
                "pass a DEM Layer or GeoTIFF path."
            )
        return _hillshade_array(dem, resolution, azimuth, altitude)
    src = open_raster(dem)
    return derived_layer(
        "hillshade",
        _hillshade_array(src.array_2d, src.resolution, azimuth, altitude),
        src,
        processing={"op": "hillshade", "azimuth": azimuth, "altitude": altitude},
    )
