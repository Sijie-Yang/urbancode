"""Fetch Sentinel-2, DEM, and derived raster layers into a City."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from urbancode.cache import imagery_dir
from urbancode.city import City, Layer, handle_layer_error
from urbancode.errors import require_extra
from urbancode.imagery.grid import stack_to_reference
from urbancode.imagery.indices import ndbi, ndvi, ndwi
from urbancode.imagery.read import read
from urbancode.imagery.stac import (
    DEFAULT_CLOUD,
    DEFAULT_MAX_PIXELS,
    DEM_COLLECTION,
    SCL_CLOUD,
    SENTINEL2_COLLECTION,
    SENTINEL_ASSETS,
    apply_scl_mask,
    covering_date_items,
    default_time_range,
    download_assets_windowed,
    layer_cache_dir,
    resolve_bbox,
    search_items,
)
from urbancode.imagery.terrain import aspect_degrees, hillshade, slope_degrees
from urbancode.imagery.write import INDEX_NODATA, parent_grid, write_geotiff

IMAGERY_LAYERS = (
    "sentinel2",
    "dem",
    "ndvi",
    "ndwi",
    "ndbi",
    "slope",
    "aspect",
    "hillshade",
)
_DERIVED = {
    "ndvi": "sentinel2",
    "ndwi": "sentinel2",
    "ndbi": "sentinel2",
    "slope": "dem",
    "aspect": "dem",
    "hillshade": "dem",
}


def fetch(
    place: str | None = None,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    layers: str | Iterable[str] | None = None,
    datetime: str | None = None,
    time: str | None = None,
    cloud: int = DEFAULT_CLOUD,
    composite: str = "single",
    max_pixels: int = DEFAULT_MAX_PIXELS,
    on_error: str = "raise",
    refresh: bool = False,
) -> City:
    """Download or derive imagery layers.

    ``time`` defaults to the last 12 months. ``composite`` is ``single``
    (least-cloudy covering tiles, mosaicked) or ``median``.
    """
    names = _normalize(layers)
    interval = time or datetime or default_time_range()
    if composite == "median":
        raise NotImplementedError(
            "composite='median' is reserved; use composite='single' "
            "(least-cloudy covering tiles, mosaicked)"
        )
    if composite != "single":
        raise ValueError("composite must be 'single' or 'median'")
    city = City(
        place=place,
        metadata={
            "time": interval,
            "cloud": cloud,
            "composite": composite,
        },
    )
    bounds = resolve_bbox(place, bbox)
    city.metadata["bbox"] = list(bounds)

    needed = set(names)
    for name in list(names):
        parent = _DERIVED.get(name)
        if parent:
            needed.add(parent)

    order = [n for n in IMAGERY_LAYERS if n in needed]
    for name in order:
        try:
            if name == "sentinel2":
                city.add_layer(
                    "sentinel2",
                    **_fetch_sentinel(
                        bounds,
                        time=interval,
                        cloud=cloud,
                        composite=composite,
                        max_pixels=max_pixels,
                        refresh=refresh,
                    ),
                    overwrite=True,
                )
            elif name == "dem":
                city.add_layer(
                    "dem",
                    **_fetch_dem(bounds, max_pixels=max_pixels, refresh=refresh),
                    overwrite=True,
                )
            elif name in {"ndvi", "ndwi", "ndbi"}:
                city.add_layer(name, **_index_layer(city, name), overwrite=True)
            elif name in {"slope", "aspect", "hillshade"}:
                city.add_layer(name, **_terrain_layer(city, name), overwrite=True)
        except Exception as exc:
            handle_layer_error(city, name, exc, on_error)
    return city


def _normalize(layers: str | Iterable[str] | None) -> list[str]:
    if layers is None:
        return ["sentinel2"]
    if isinstance(layers, str):
        layers = [part.strip() for part in layers.split(",") if part.strip()]
    names = list(layers)
    unknown = [n for n in names if n not in IMAGERY_LAYERS]
    if unknown:
        raise ValueError(f"unknown imagery layers {unknown}; known: {list(IMAGERY_LAYERS)}")
    return names


def _fetch_sentinel(
    bbox: tuple[float, float, float, float],
    *,
    time: str,
    cloud: int,
    composite: str,
    max_pixels: int,
    refresh: bool,
) -> dict[str, Any]:
    dest = layer_cache_dir("sentinel2", bbox, time, cloud, composite)
    stacked_path = dest / "stack.tif"
    meta_path = dest / "metadata.json"
    if stacked_path.exists() and meta_path.exists() and not refresh:
        stored = _read_cache_metadata(meta_path, stacked_path)
        if stored is not None:
            layer = read(stacked_path, name="sentinel2")
            return {
                "data": layer.data,
                "kind": "raster",
                "path": str(stacked_path),
                "crs": layer.crs,
                "source": SENTINEL2_COLLECTION,
                "metadata": stored,
            }

    items = search_items(SENTINEL2_COLLECTION, bbox, datetime=time, cloud=cloud)
    if composite == "single":
        chosen = covering_date_items(items, bbox)
    else:
        chosen = items[:12]
    paths = download_assets_windowed(
        chosen,
        list(SENTINEL_ASSETS) + ["SCL"],
        dest,
        bbox,
        max_pixels=max_pixels,
    )
    optical = {k: v for k, v in paths.items() if k in SENTINEL_ASSETS}
    stacked = stack_to_reference(optical, stacked_path, reference="B08")
    if "SCL" in paths and "B08" in optical:
        from urbancode.imagery.grid import reproject_to_reference

        scl_aligned = dest / "SCL_10m.tif"
        reproject_to_reference(
            paths["SCL"],
            scl_aligned,
            reference_path=optical["B08"],
            resampling="nearest",
        )
        _mask_stack_with_scl(stacked, scl_aligned)

    layer = read(stacked, name="sentinel2")
    meta = dict(layer.metadata)
    meta.update(
        {
            "datetime": chosen[0].properties.get("datetime") if chosen else None,
            "source": SENTINEL2_COLLECTION,
            "license": "various",
            "item_ids": [it.id for it in chosen],
            "checksum": _file_sha256(stacked),
            "processing": {
                "cloud_lt": cloud,
                "composite": composite,
                "reference_band": "B08",
                "resampling": "bilinear",
                "scl_mask": list(SCL_CLOUD) if "SCL" in paths else None,
                "windowed": True,
                "time": time,
            },
        }
    )
    meta_path.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    return {
        "data": layer.data,
        "kind": "raster",
        "path": str(stacked),
        "crs": layer.crs,
        "source": SENTINEL2_COLLECTION,
        "metadata": meta,
    }


def _file_sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_cache_metadata(meta_path: Path, stacked_path: Path) -> dict[str, Any] | None:
    try:
        stored = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    expected = stored.get("checksum")
    if not expected or expected != _file_sha256(stacked_path):
        return None
    return stored


def _mask_stack_with_scl(stack_path: Path, scl_path: Path) -> None:
    rasterio = require_extra("rasterio", "imagery")
    with rasterio.open(stack_path) as src:
        stack = src.read()
        profile = src.profile
        transform = src.transform
        crs = src.crs
        names = [src.descriptions[i] or f"B{i+1}" for i in range(src.count)]
    with rasterio.open(scl_path) as src:
        scl = src.read(1)
    masked = apply_scl_mask(stack, scl)
    write_geotiff(
        masked,
        stack_path,
        transform=transform,
        crs=crs,
        nodata=float("nan"),
        dtype=np.float32,
        band_names=names,
    )
    del profile


def _fetch_dem(
    bbox: tuple[float, float, float, float],
    *,
    max_pixels: int,
    refresh: bool,
) -> dict[str, Any]:
    dest = layer_cache_dir("dem", bbox)
    out = dest / "dem.tif"
    if out.exists() and not refresh:
        return _layer_kwargs(read(out, name="dem"), DEM_COLLECTION)
    items = search_items(DEM_COLLECTION, bbox, datetime=None, cloud=None)
    paths = download_assets_windowed(
        items[:8],
        ("data", "dem"),
        dest,
        bbox,
        max_pixels=max_pixels,
    )
    src = next(iter(paths.values()))
    if src.resolve() != out.resolve():
        import shutil

        shutil.copy2(src, out)
    layer = read(out, name="dem")
    meta = dict(layer.metadata)
    meta.update(
        {
            "source": DEM_COLLECTION,
            "license": "Copernicus DEM",
            "item_ids": [it.id for it in items[:8]],
            "processing": {"windowed": True},
        }
    )
    return {
        "data": layer.data,
        "kind": "raster",
        "path": str(out),
        "crs": layer.crs,
        "source": DEM_COLLECTION,
        "metadata": meta,
    }


def _layer_kwargs(layer: Layer, source: str) -> dict[str, Any]:
    return {
        "data": layer.data,
        "kind": "raster",
        "path": layer.path,
        "crs": layer.crs,
        "source": source,
        "metadata": layer.metadata,
    }


def _index_layer(city: City, name: str) -> dict[str, Any]:
    parent = city.layer("sentinel2")
    bands = _named_bands(parent)
    fn = {"ndvi": ndvi, "ndwi": ndwi, "ndbi": ndbi}[name]
    array = fn(bands, nodata=float(INDEX_NODATA))
    return _write_derived(
        name,
        array,
        parent,
        processing={"index": name, "nodata": "nan"},
        dtype=np.float32,
        nodata=float("nan"),
    )


def _terrain_layer(city: City, name: str) -> dict[str, Any]:
    parent = city.layer("dem")
    projected, res_m, work_crs = _dem_in_meters(parent)
    dem = _first_band_values(projected)
    if name == "slope":
        array = slope_degrees(dem, res_m)
        dtype: Any = np.float32
        nodata: float | None = float("nan")
    elif name == "aspect":
        array = aspect_degrees(dem, res_m)
        dtype = np.float32
        nodata = float("nan")
    else:
        array = hillshade(dem, res_m).astype(np.uint8)
        dtype = np.uint8
        nodata = None
    parent_like = Layer(
        name=parent.name,
        kind="raster",
        data=projected,
        path=parent.path,
        crs=work_crs,
        source=parent.source,
        metadata=dict(parent.metadata),
    )
    return _write_derived(
        name,
        array,
        parent_like,
        processing={
            "derived": name,
            "working_crs": str(work_crs),
            "resolution_m": res_m,
            "algorithm": "numpy.gradient",
        },
        dtype=dtype,
        nodata=nodata,
    )


def _dem_in_meters(layer: Layer) -> tuple[Any, float, Any]:
    """Reproject a DEM to a local metric CRS before slope/aspect."""
    require_extra("rasterio", "imagery")
    rxr = require_extra("rioxarray", "imagery")
    da = layer.data
    if da is None and layer.path:
        da = rxr.open_rasterio(layer.path, masked=True)
    if not hasattr(da, "rio"):
        raise ValueError("DEM layer must be a georeferenced raster")
    crs = da.rio.crs
    if crs is not None and getattr(crs, "is_geographic", False):
        utm = da.rio.estimate_utm_crs()
        da = da.rio.reproject(utm)
        crs = utm
    res = da.rio.resolution()
    res_m = float(abs(res[0]))
    if res_m <= 0:
        raise ValueError("DEM resolution must be positive")
    return da, res_m, crs


def _write_derived(
    name: str,
    array: np.ndarray,
    parent: Layer,
    *,
    processing: dict[str, Any],
    dtype: Any,
    nodata: float | None,
) -> dict[str, Any]:
    grid = parent_grid(parent)
    dest = imagery_dir() / "derived" / f"{name}_{_safe_stamp()}.tif"
    write_geotiff(
        array,
        dest,
        transform=grid["transform"],
        crs=grid["crs"],
        nodata=nodata,
        dtype=dtype,
        band_names=[name],
    )
    layer = read(dest, name=name)
    meta = dict(layer.metadata)
    meta.update(
        {
            "datetime": datetime.now(timezone.utc).isoformat(),
            "processing": processing,
            "parent": parent.name,
            "source": parent.source,
        }
    )
    return {
        "data": layer.data,
        "kind": "raster",
        "path": str(dest),
        "crs": layer.crs,
        "source": parent.source,
        "metadata": meta,
    }


def _safe_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")


def _named_bands(layer: Layer) -> dict[str, np.ndarray]:
    data = layer.data
    names = list(layer.metadata.get("bands") or [])
    values = np.asarray(getattr(data, "values", data))
    if values.ndim == 2:
        key = names[0] if names else "band1"
        return {key: values}
    bands: dict[str, np.ndarray] = {}
    alias = {"B04": "red", "B08": "nir", "B03": "green", "B11": "swir"}
    for i in range(values.shape[0]):
        key = names[i] if i < len(names) else f"B{i+1:02d}"
        # rioxarray band coords may be 1..N; prefer GeoTIFF descriptions.
        if str(key).isdigit() and layer.path:
            key = _band_description(layer.path, i) or key
        bands[str(key)] = values[i]
        if str(key) in alias:
            bands[alias[str(key)]] = values[i]
    return bands


def _band_description(path: str, index: int) -> str | None:
    rasterio = require_extra("rasterio", "imagery")
    with rasterio.open(path) as src:
        desc = src.descriptions[index] if index < src.count else None
    return desc or None


def _first_band_values(data: Any) -> np.ndarray:
    values = np.asarray(getattr(data, "values", data))
    if values.ndim == 3:
        return values[0]
    return values
