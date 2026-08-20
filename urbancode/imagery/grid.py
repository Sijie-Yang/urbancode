"""Align rasters onto a shared reference grid."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from urbancode.errors import require_extra
from urbancode.imagery.write import write_geotiff


def reproject_to_reference(
    src_path: Path,
    dest: Path,
    *,
    reference_path: Path,
    resampling: str = "bilinear",
) -> Path:
    """Warp one raster onto another raster's grid."""
    rasterio = require_extra("rasterio", "imagery")
    from rasterio.enums import Resampling
    from rasterio.warp import reproject

    how = Resampling.bilinear if resampling == "bilinear" else Resampling.nearest
    with rasterio.open(reference_path) as ref, rasterio.open(src_path) as src:
        dest_arr = np.zeros((ref.height, ref.width), dtype=np.float32)
        reproject(
            source=src.read(1),
            destination=dest_arr,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=ref.transform,
            dst_crs=ref.crs,
            resampling=how,
            src_nodata=src.nodata,
            dst_nodata=np.nan,
        )
        write_geotiff(
            dest_arr,
            dest,
            transform=ref.transform,
            crs=ref.crs,
            nodata=float("nan"),
            dtype=np.float32,
            band_names=[src.descriptions[0] or src_path.stem],
        )
    return dest


def stack_to_reference(
    paths: dict[str, Path],
    dest: Path,
    *,
    reference: str = "B08",
    fallback_reference: str = "B04",
    resampling: str = "bilinear",
) -> Path:
    """Stack named band files onto the reference band's  grid.

    20 m assets (e.g. B11) are bilinear-resampled. Shapes are never assumed equal.
    """
    rasterio = require_extra("rasterio", "imagery")
    from rasterio.enums import Resampling
    from rasterio.warp import reproject

    if reference not in paths:
        reference = fallback_reference if fallback_reference in paths else next(iter(paths))
    names = list(paths)
    with rasterio.open(paths[reference]) as ref:
        dst_crs = ref.crs
        dst_transform = ref.transform
        height, width = ref.height, ref.width
        ref_profile = ref.profile

    how = Resampling.bilinear if resampling == "bilinear" else Resampling.nearest
    bands: list[np.ndarray] = []
    for name in names:
        with rasterio.open(paths[name]) as src:
            dest_arr = np.zeros((height, width), dtype=np.float32)
            reproject(
                source=src.read(1),
                destination=dest_arr,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=dst_transform,
                dst_crs=dst_crs,
                resampling=how,
                src_nodata=src.nodata,
                dst_nodata=np.nan,
            )
            bands.append(dest_arr)

    stacked = np.stack(bands, axis=0)
    write_geotiff(
        stacked,
        dest,
        transform=dst_transform,
        crs=dst_crs,
        nodata=float("nan"),
        dtype=np.float32,
        band_names=names,
    )
    del ref_profile
    return dest
