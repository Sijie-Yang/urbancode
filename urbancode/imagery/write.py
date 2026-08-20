"""Write georeferenced GeoTIFFs. Derived layers must not reuse a parent path."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import numpy as np

from urbancode.errors import require_extra

INDEX_NODATA = np.float32(np.nan)


def write_geotiff(
    array: np.ndarray,
    dest: str | Path,
    *,
    transform: Any,
    crs: Any,
    nodata: float | None = None,
    dtype: str | np.dtype | None = None,
    band_names: Sequence[str] | None = None,
) -> Path:
    """Write ``array`` (2-D or 3-D band-first) to ``dest`` with a geotransform."""
    rasterio = require_extra("rasterio", "imagery")
    from rasterio.crs import CRS

    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    data = np.asarray(array)
    if data.ndim == 2:
        data = data[np.newaxis, ...]
    if data.ndim != 3:
        raise ValueError(f"expected 2-D or 3-D array, got shape {data.shape}")
    count, height, width = data.shape
    out_dtype = np.dtype(dtype) if dtype is not None else data.dtype
    if out_dtype == np.float64:
        out_dtype = np.dtype(np.float32)
        data = data.astype(np.float32)
    elif data.dtype != out_dtype:
        data = data.astype(out_dtype)

    crs_obj = crs
    if crs is not None and not isinstance(crs, CRS):
        crs_obj = CRS.from_user_input(str(crs))
    if isinstance(transform, (list, tuple)) and len(transform) >= 6:
        from rasterio.transform import Affine

        transform = Affine(*[float(v) for v in transform[:6]])

    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": count,
        "dtype": str(out_dtype),
        "crs": crs_obj,
        "transform": transform,
        "compress": "deflate",
    }
    if nodata is not None and not (isinstance(nodata, float) and np.isnan(nodata)):
        profile["nodata"] = nodata
    elif nodata is not None and np.isnan(nodata) and np.issubdtype(out_dtype, np.floating):
        profile["nodata"] = float("nan")

    with rasterio.open(dest_path, "w", **profile) as dst:
        dst.write(data)
        if band_names:
            for i, name in enumerate(band_names, start=1):
                if i <= count:
                    dst.set_band_description(i, str(name))
    return dest_path


def parent_grid(layer: Any) -> dict[str, Any]:
    """CRS / transform / shape from a Layer with rio data or a GeoTIFF path."""
    rasterio = require_extra("rasterio", "imagery")
    data = getattr(layer, "data", None)
    rio = getattr(data, "rio", None)
    if rio is not None:
        height = int(getattr(rio, "height", 0) or data.rio.shape[-2])
        width = int(getattr(rio, "width", 0) or data.rio.shape[-1])
        return {
            "transform": rio.transform(),
            "crs": rio.crs,
            "height": height,
            "width": width,
            "nodata": rio.nodata,
        }
    path = getattr(layer, "path", None)
    if path and Path(path).exists():
        with rasterio.open(path) as src:
            return {
                "transform": src.transform,
                "crs": src.crs,
                "height": src.height,
                "width": src.width,
                "nodata": src.nodata,
            }
    raise ValueError(
        "cannot inherit a raster grid: layer has no rioxarray data or GeoTIFF path"
    )
