"""Satellite, DEM, and local raster analysis."""

from typing import Any

from urbancode.imagery.fetch import fetch
from urbancode.imagery.indices import ndbi, ndvi, ndwi
from urbancode.imagery.read import read
from urbancode.imagery.terrain import aspect, aspect_degrees, hillshade, slope, slope_degrees
from urbancode.imagery.zonal import zonal_stats

__all__ = [
    "aspect",
    "aspect_degrees",
    "fetch",
    "hillshade",
    "ndbi",
    "ndvi",
    "ndwi",
    "read",
    "slope",
    "slope_degrees",
    "utci",
    "zonal_stats",
]


def __getattr__(name: str) -> Any:
    if name == "utci":
        from urbancode.climate.thermal import utci

        globals()["utci"] = utci
        return utci
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
