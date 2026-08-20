"""Zonal statistics of a georeferenced raster against vector zones."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import numpy as np

from urbancode.city import Layer
from urbancode.errors import require_extra


def zonal_stats(
    raster: Any,
    zones: Any,
    metrics: Sequence[str] = ("mean", "p50"),
    band: int = 0,
) -> Any:
    """Summarize a georeferenced raster inside each zone geometry.

    A Layer raster returns a vector :class:`~urbancode.city.Layer` so the
    result can be plotted. A file path, rasterio dataset, or DataArray
    still returns a GeoDataFrame.
    """
    rasterio = require_extra("rasterio", "imagery")
    from rasterio.features import rasterize

    require_extra("geopandas", "vector")
    zones_gdf = _as_zones(zones)
    if not hasattr(zones_gdf, "geometry"):
        raise TypeError("zones must be a Layer or GeoDataFrame")

    array, transform, nodata, raster_crs = _as_georeferenced(raster, band)
    if transform is None:
        raise ValueError(
            "zonal_stats requires a georeferenced raster (Layer, path, "
            "rasterio dataset, or rioxarray DataArray with a transform). "
            "Bare NumPy arrays are not supported."
        )
    aligned = zones_gdf
    if raster_crs is not None and getattr(zones_gdf, "crs", None) is not None:
        if str(zones_gdf.crs) != str(raster_crs):
            aligned = zones_gdf.to_crs(raster_crs)

    out = aligned.copy()
    shapes = (
        (geom, idx + 1)
        for idx, geom in enumerate(aligned.geometry)
        if geom is not None and not geom.is_empty
    )
    label = rasterize(
        shapes,
        out_shape=array.shape,
        transform=transform,
        fill=0,
        dtype="int32",
    )
    data = np.asarray(array, dtype=float)
    if nodata is not None and not (isinstance(nodata, float) and np.isnan(nodata)):
        data = np.where(data == nodata, np.nan, data)

    for metric in metrics:
        values = []
        for idx in range(len(aligned)):
            mask = label == (idx + 1)
            raw = data[mask]
            finite = raw[np.isfinite(raw)]
            if metric == "coverage":
                values.append(
                    float(finite.size) / float(raw.size) if raw.size else float("nan")
                )
            else:
                values.append(_metric(finite, metric))
        out[metric] = values

    if isinstance(raster, Layer):
        from urbancode.provenance import stamp_layer

        layer = Layer(
            name="zonal_stats",
            kind="vector",
            data=out,
            crs=getattr(out, "crs", None),
            source="urbancode.imagery.zonal_stats",
            metadata={
                "processing": {"op": "zonal_stats", "metrics": list(metrics)},
                "column": list(metrics)[0] if metrics else None,
                "parent": raster.name,
            },
        )
        stamp_layer(layer)
        return layer
    return out


def _as_zones(zones: Any) -> Any:
    if isinstance(zones, Layer):
        if zones.data is not None and hasattr(zones.data, "geometry"):
            return zones.data
        raise TypeError(f"zone layer {zones.name!r} is not a GeoDataFrame")
    return zones


def _as_georeferenced(
    raster: Any, band: int
) -> tuple[np.ndarray, Any, Any, Any]:
    rasterio = require_extra("rasterio", "imagery")
    if isinstance(raster, Layer):
        from urbancode.imagery.source import as_affine, open_raster

        src = open_raster(raster)
        values = np.asarray(src.array if src.array is not None else src.array_2d)
        if values.ndim == 3:
            values = values[band]
        return values, as_affine(src.transform), src.nodata, src.crs
    if isinstance(raster, (str, bytes, Path)):
        with rasterio.open(raster) as src:
            return src.read(band + 1), src.transform, src.nodata, src.crs
    if hasattr(raster, "read") and hasattr(raster, "transform"):
        return (
            raster.read(band + 1),
            raster.transform,
            getattr(raster, "nodata", None),
            getattr(raster, "crs", None),
        )
    if hasattr(raster, "rio"):
        values = np.asarray(raster.values)
        if values.ndim == 3:
            values = values[band]
        return values, raster.rio.transform(), raster.rio.nodata, raster.rio.crs
    raise ValueError(
        "zonal_stats requires a georeferenced raster; got "
        f"{type(raster).__name__}"
    )


def _metric(pixels: np.ndarray, name: str) -> float:
    if pixels.size == 0:
        return float("nan")
    if name == "mean":
        return float(np.mean(pixels))
    if name == "min":
        return float(np.min(pixels))
    if name == "max":
        return float(np.max(pixels))
    if name == "std":
        return float(np.std(pixels))
    if name == "p50" or name == "median":
        return float(np.median(pixels))
    if name == "sum":
        return float(np.sum(pixels))
    if name == "count":
        return float(pixels.size)
    raise ValueError(f"unknown metric {name!r}")
