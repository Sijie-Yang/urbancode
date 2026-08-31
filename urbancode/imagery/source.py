"""Coerce Layer / path / DataArray inputs into a georeferenced raster."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from urbancode.city import Layer
from urbancode.errors import require_extra


@dataclass
class RasterSource:
    """Named bands plus the grid a derived Layer must inherit."""

    bands: dict[str, np.ndarray]
    transform: Any
    crs: Any
    nodata: Any
    resolution: float
    name: str = "raster"
    path: str | None = None
    band_names: list[str] = field(default_factory=list)
    parent: str | None = None
    array: np.ndarray | None = None

    @property
    def resolution_xy(self) -> tuple[float, float]:
        transform = self.transform
        if transform is None:
            return self.resolution, self.resolution
        if hasattr(transform, "a"):
            return float(abs(transform.a)), float(abs(transform.e))
        if isinstance(transform, (list, tuple)) and len(transform) >= 6:
            return float(abs(transform[0])), float(abs(transform[4]))
        return self.resolution, self.resolution

    @property
    def array_2d(self) -> np.ndarray:
        if self.array is not None:
            values = np.asarray(self.array)
            if values.ndim == 3:
                return values[0]
            if values.ndim == 2:
                return values
        if self.bands:
            return np.asarray(next(iter(self.bands.values())))
        raise ValueError("raster has no array")


def is_band_map(source: Any) -> bool:
    """True for the low-level ``{name: ndarray}`` index API."""
    if isinstance(source, (str, Path, bytes, Layer)):
        return False
    if hasattr(source, "rio"):
        return False
    if isinstance(source, dict):
        values = list(source.values())
        return bool(values) and all(hasattr(item, "shape") for item in values)
    return False


def is_numeric_array(source: Any) -> bool:
    return isinstance(source, np.ndarray)


def affine_to_list(transform: Any) -> list[float] | None:
    if transform is None:
        return None
    if isinstance(transform, (list, tuple)):
        return [float(v) for v in transform[:6]]
    return [
        float(transform.a),
        float(transform.b),
        float(transform.c),
        float(transform.d),
        float(transform.e),
        float(transform.f),
    ]


def as_affine(transform: Any) -> Any:
    if transform is None or hasattr(transform, "a"):
        return transform
    if isinstance(transform, (list, tuple)) and len(transform) >= 6:
        rasterio = require_extra("rasterio", "imagery")
        return rasterio.Affine(*[float(v) for v in transform[:6]])
    return transform


def open_raster(source: Any) -> RasterSource:
    """Accept a Layer, GeoTIFF path, or rioxarray DataArray."""
    if isinstance(source, Layer):
        return _from_layer(source)
    if isinstance(source, (str, Path)):
        return _from_path(source)
    if hasattr(source, "rio"):
        return _from_dataarray(source)
    raise TypeError(
        f"expected a Layer, GeoTIFF path, or DataArray; got {type(source).__name__}. "
        "For raw arrays use ndvi({'B04': red, 'B08': nir}) or "
        "slope_degrees(array, resolution)."
    )


def derived_layer(
    name: str,
    array: np.ndarray,
    src: RasterSource,
    *,
    nodata: float = float("nan"),
    processing: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> Layer:
    """Wrap a derived 2-D array as a plottable raster Layer."""
    transform = src.transform
    transform_list = affine_to_list(transform)
    metadata = {
        "transform": transform_list,
        "nodata": nodata,
        "processing": dict(processing or {}),
        "parent": src.parent or src.name,
        "resolution": src.resolution,
    }
    if extra:
        metadata.update(extra)
    layer = Layer(
        name=name,
        kind="raster",
        data=np.asarray(array),
        path=None,
        crs=src.crs,
        source=src.path,
        metadata=metadata,
    )
    from urbancode.provenance import stamp_layer

    stamp_layer(layer)
    return layer


def _from_layer(layer: Layer) -> RasterSource:
    path = layer.path
    if path and Path(path).exists():
        src = _from_path(path)
        src.name = layer.name
        src.parent = layer.name
        return src
    data = layer.data
    if isinstance(data, (str, Path)) and Path(str(data)).exists():
        src = _from_path(data)
        src.name = layer.name
        src.parent = layer.name
        return src
    if hasattr(data, "rio"):
        src = _from_dataarray(data)
        src.name = layer.name
        src.parent = layer.name
        return src
    if isinstance(data, np.ndarray):
        transform = as_affine(layer.metadata.get("transform"))
        if transform is None:
            raise ValueError(
                f"layer {layer.name!r} is an in-memory raster without a transform. "
                "Pass a GeoTIFF path or a Layer produced by uc.imagery.ndvi / slope."
            )
        values = np.asarray(data)
        return RasterSource(
            bands={layer.name: values if values.ndim == 2 else values[0]},
            transform=transform,
            crs=layer.crs,
            nodata=layer.metadata.get("nodata", np.nan),
            resolution=float(abs(transform.a)),
            name=layer.name,
            path=layer.path,
            band_names=[layer.name],
            parent=layer.metadata.get("parent"),
            array=values,
        )
    raise TypeError(
        f"layer {layer.name!r} has no GeoTIFF path or georeferenced array"
    )


def _from_path(path: str | Path) -> RasterSource:
    rasterio = require_extra("rasterio", "imagery")
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    with rasterio.open(file_path) as src:
        names = [
            str(desc) if desc else f"band{i}"
            for i, desc in enumerate(src.descriptions, start=1)
        ]
        bands = {names[i]: src.read(i + 1) for i in range(src.count)}
        array = src.read(1) if src.count == 1 else src.read()
        return RasterSource(
            bands=bands,
            transform=src.transform,
            crs=src.crs,
            nodata=src.nodata,
            resolution=float(abs(src.transform.a)),
            name=file_path.stem,
            path=str(file_path),
            band_names=names,
            parent=file_path.stem,
            array=array,
        )


def _from_dataarray(da: Any) -> RasterSource:
    encoding = getattr(da, "encoding", None) or {}
    source_path = encoding.get("source")
    if source_path and Path(str(source_path)).exists():
        return _from_path(source_path)

    values = np.asarray(da.values)
    names = _dataarray_band_names(da, values)
    if values.ndim == 3:
        bands = {names[i]: values[i] for i in range(min(len(names), values.shape[0]))}
        array = values
    elif values.ndim == 2:
        bands = {names[0] if names else "band1": values}
        array = values
    else:
        raise ValueError(f"expected a 2-D or 3-D DataArray, got shape {values.shape}")

    rio = da.rio
    transform = rio.transform()
    return RasterSource(
        bands=bands,
        transform=transform,
        crs=rio.crs,
        nodata=rio.nodata,
        resolution=float(abs(transform.a)),
        name=str(getattr(da, "name", None) or "raster"),
        path=str(source_path) if source_path else None,
        band_names=list(bands),
        parent=str(getattr(da, "name", None) or "raster"),
        array=array,
    )


def _dataarray_band_names(da: Any, values: np.ndarray) -> list[str]:
    long_name = getattr(da, "long_name", None)
    if isinstance(long_name, str) and long_name:
        names = [long_name]
    elif isinstance(long_name, (list, tuple)) and long_name:
        names = [str(item) for item in long_name]
    elif "band" in getattr(da, "coords", {}):
        names = [str(v) for v in da.coords["band"].values]
    else:
        names = []
    count = values.shape[0] if values.ndim == 3 else 1
    if len(names) < count:
        names = names + [f"band{i}" for i in range(len(names) + 1, count + 1)]
    return names
