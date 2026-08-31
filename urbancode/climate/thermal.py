"""Outdoor thermal indices. Needs urbancode[climate]."""

from __future__ import annotations

from typing import Any

import numpy as np

from urbancode.city import Layer
from urbancode.errors import require_extra
from urbancode.imagery.source import derived_layer, is_numeric_array, open_raster


def utci(
    tdb: Any = None,
    tr: Any | None = None,
    v: Any | None = None,
    rh: Any | None = None,
    *,
    air_temperature: Any | None = None,
    mean_radiant_temperature: Any | None = None,
    wind_speed: Any | None = None,
    relative_humidity: Any | None = None,
) -> np.ndarray | Layer:
    """Compute the Universal Thermal Climate Index in degrees Celsius.

    Args:
        tdb: Dry-bulb air temperature in °C. Alias: ``air_temperature``.
        tr: Mean radiant temperature in °C. Defaults to ``tdb``. Alias:
            ``mean_radiant_temperature``.
        v: Wind speed in m/s. Defaults to 0.5. Alias: ``wind_speed``.
        rh: Relative humidity in percent. Defaults to 50. Alias:
            ``relative_humidity``.
        air_temperature: Keyword alias for ``tdb``.
        mean_radiant_temperature: Keyword alias for ``tr``.
        wind_speed: Keyword alias for ``v``.
        relative_humidity: Keyword alias for ``rh``.

    Returns:
        A NumPy array for scalar/array inputs, or a raster
        :class:`~urbancode.city.Layer` when ``tdb`` is a georeferenced Layer or
        GeoTIFF path. Raster output inherits the air-temperature grid and
        records any defaulted inputs as quality flags.

    Raises:
        TypeError: If air temperature is missing.
        urbancode.errors.MissingExtraError: If ``urbancode[climate]`` is not
            installed.

    Notes:
        UTCI is a thermal index, not medical advice. Copying air temperature to
        radiant temperature is an explicit assumption, not a measurement.
    """
    comfort = require_extra("pythermalcomfort.models", "climate")
    tdb = air_temperature if tdb is None else tdb
    if tdb is None:
        raise TypeError("utci requires tdb= or air_temperature=")
    tr = mean_radiant_temperature if tr is None else tr
    v = wind_speed if v is None else v
    rh = relative_humidity if rh is None else rh
    defaults = []
    if tr is None:
        defaults.append("mean_radiant_temperature=air_temperature")
    if v is None:
        defaults.append("wind_speed=0.5")
    if rh is None:
        defaults.append("relative_humidity=50")
    air = _numeric(tdb)
    radiant = _numeric(tr) if tr is not None else air
    wind = _numeric(v) if v is not None else 0.5
    humidity = _numeric(rh) if rh is not None else 50.0
    result = comfort.utci(tdb=air, tr=radiant, v=wind, rh=humidity)
    values = np.asarray(getattr(result, "utci", result), dtype=float)
    if is_numeric_array(tdb) or isinstance(tdb, (int, float, np.floating, np.integer)):
        return values
    src = open_raster(tdb)
    return derived_layer(
        "utci",
        values.reshape(src.array_2d.shape)
        if values.ndim == 1 and src.array_2d.size == values.size
        else values,
        src,
        processing={
            "op": "utci",
            "definition": "universal_thermal_climate_index",
            "backend": "pythermalcomfort",
            "assumptions": defaults,
        },
        extra={"unit": "degree_celsius", "quality_flags": defaults},
    )


def _numeric(source: Any) -> Any:
    if source is None:
        raise TypeError("value is required")
    if isinstance(source, (int, float, np.floating, np.integer)):
        return float(source)
    if is_numeric_array(source):
        return np.asarray(source, dtype=float)
    return np.asarray(open_raster(source).array_2d, dtype=float)
