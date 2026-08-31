"""STAC helpers: windowed reads, mosaic, and search (Planetary Computer)."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from urbancode.cache import imagery_dir
from urbancode.errors import (
    RasterDoesNotIntersectError,
    RasterSizeLimitError,
    require_extra,
)
from urbancode.geocode import geocode_bbox
from urbancode.imagery.write import write_geotiff

PC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
SENTINEL2_COLLECTION = "sentinel-2-l2a"
DEM_COLLECTION = "cop-dem-glo-30"
SENTINEL_ASSETS = ("B02", "B03", "B04", "B08", "B11")
SCL_CLOUD = frozenset({3, 8, 9, 10})  # shadow, med/high cloud, cirrus
DEFAULT_MAX_PIXELS = 25_000_000
DEFAULT_CLOUD = 20


def default_time_range() -> str:
    """Last 12 months as a STAC datetime interval."""
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=365)
    return f"{start.isoformat()}/{end.isoformat()}"


def resolve_bbox(
    place: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> tuple[float, float, float, float]:
    """Return ``(west, south, east, north)`` without requiring osmnx."""
    if bbox is not None:
        return tuple(float(v) for v in bbox)  # type: ignore[return-value]
    if not place:
        raise ValueError("place or bbox is required")
    return geocode_bbox(place)


def _client():
    pystac_client = require_extra("pystac_client", "imagery")
    return pystac_client.Client.open(PC_URL)


def _sign(item: Any) -> Any:
    pc = require_extra("planetary_computer", "imagery")
    return pc.sign(item)


def search_items(
    collection: str,
    bbox: tuple[float, float, float, float],
    *,
    datetime: str | None = None,
    cloud: int | None = DEFAULT_CLOUD,
    limit: int = 40,
) -> list[Any]:
    """Return STAC items covering the AOI (not a single global least-cloudy scene)."""
    client = _client()
    kwargs: dict[str, Any] = {
        "collections": [collection],
        "bbox": list(bbox),
        "max_items": limit,
    }
    # Copernicus DEM is a static mosaic; do not apply the Sentinel 12-month window.
    if collection != DEM_COLLECTION:
        kwargs["datetime"] = datetime or default_time_range()
    elif datetime:
        kwargs["datetime"] = datetime
    query: dict[str, Any] = {}
    if cloud is not None and collection == SENTINEL2_COLLECTION:
        query["eo:cloud_cover"] = {"lt": cloud}
    if query:
        kwargs["query"] = query
    search = client.search(**kwargs)
    items = list(search.items())
    if not items:
        raise FileNotFoundError(
            f"no STAC items in {collection} for bbox={bbox} "
            f"datetime={kwargs.get('datetime')}"
        )
    items.sort(
        key=lambda it: (
            it.properties.get("eo:cloud_cover", 100),
            it.properties.get("datetime") or "",
        )
    )
    return items


def search_item(
    collection: str,
    bbox: tuple[float, float, float, float],
    *,
    datetime: str | None = None,
    query: dict[str, Any] | None = None,
) -> Any:
    """Back-compat: first item from :func:`search_items`."""
    cloud = None
    if query and "eo:cloud_cover" in query:
        cloud = int(query["eo:cloud_cover"].get("lt", DEFAULT_CLOUD))
    return search_items(collection, bbox, datetime=datetime, cloud=cloud)[0]


def windowed_read(
    href: str,
    bbox: tuple[float, float, float, float],
    *,
    max_pixels: int = DEFAULT_MAX_PIXELS,
    indexes: int | Sequence[int] = 1,
) -> tuple[np.ndarray, Any, Any, dict[str, Any]]:
    """Read only the window covering ``bbox`` (WGS84). Never ``src.read()`` a full tile."""
    rasterio = require_extra("rasterio", "imagery")
    from rasterio.warp import transform_bounds
    from rasterio.windows import Window, from_bounds

    with rasterio.open(href) as src:
        left, bottom, right, top = transform_bounds(
            "EPSG:4326", src.crs, *bbox, densify_pts=21
        )
        window = from_bounds(left, bottom, right, top, transform=src.transform)
        window = window.round_offsets().round_lengths()
        window = window.intersection(Window(0, 0, src.width, src.height))
        if window.width <= 0 or window.height <= 0:
            raise RasterDoesNotIntersectError(f"bbox {bbox} does not intersect {href}")
        pixels = int(window.width) * int(window.height)
        if pixels > max_pixels:
            raise RasterSizeLimitError(
                f"window is {pixels} pixels (> max_pixels={max_pixels}). "
                "Pass a smaller bbox or raise max_pixels."
            )
        data = src.read(indexes, window=window, boundless=False)
        transform = src.window_transform(window)
        profile = src.profile.copy()
        profile.update(
            {
                "height": int(window.height),
                "width": int(window.width),
                "transform": transform,
            }
        )
        return np.asarray(data), transform, src.crs, profile


def mosaic_arrays(
    pieces: list[tuple[np.ndarray, Any, Any]],
    *,
    dst_crs: Any | None = None,
    nodata: float | None = float("nan"),
    max_pixels: int | None = None,
) -> tuple[np.ndarray, Any, Any]:
    """Mosaic windowed arrays onto one CRS (first-valid merge)."""
    rasterio = require_extra("rasterio", "imagery")
    from rasterio.enums import Resampling
    from rasterio.io import MemoryFile
    from rasterio.merge import merge
    from rasterio.warp import calculate_default_transform, reproject

    if not pieces:
        raise ValueError("no windows to mosaic")

    target_crs = dst_crs or pieces[0][2]
    aligned: list[tuple[np.ndarray, Any, Any]] = []
    for arr, transform, crs in pieces:
        data = np.asarray(arr)
        if data.ndim == 2:
            data = data[np.newaxis, ...]
        if crs is None or target_crs is None or str(crs) == str(target_crs):
            aligned.append((data, transform, target_crs))
            continue
        height, width = data.shape[-2], data.shape[-1]
        dst_transform, dst_w, dst_h = calculate_default_transform(
            crs, target_crs, width, height, * _bounds_from(transform, width, height)
        )
        dest = np.full((data.shape[0], int(dst_h), int(dst_w)), np.nan, dtype=np.float32)
        for band in range(data.shape[0]):
            reproject(
                source=data[band],
                destination=dest[band],
                src_transform=transform,
                src_crs=crs,
                dst_transform=dst_transform,
                dst_crs=target_crs,
                resampling=Resampling.bilinear,
                src_nodata=nodata,
                dst_nodata=np.nan,
            )
        aligned.append((dest, dst_transform, target_crs))

    if len(aligned) == 1:
        mosaic, out_transform, out_crs = aligned[0]
    else:
        datasets = []
        memfiles = []
        try:
            for data, transform, crs in aligned:
                mem = MemoryFile()
                memfiles.append(mem)
                profile = {
                    "driver": "GTiff",
                    "height": data.shape[1],
                    "width": data.shape[2],
                    "count": data.shape[0],
                    "dtype": str(data.dtype),
                    "crs": crs,
                    "transform": transform,
                }
                if nodata is not None and not (
                    isinstance(nodata, float) and np.isnan(nodata)
                ):
                    profile["nodata"] = nodata
                dst = mem.open(**profile)
                dst.write(data)
                datasets.append(dst)
            mosaic, out_transform = merge(datasets, nodata=nodata)
            out_crs = target_crs
        finally:
            for ds in datasets:
                ds.close()
            for mem in memfiles:
                mem.close()

    n_bands = int(mosaic.shape[0]) if mosaic.ndim == 3 else 1
    height, width = mosaic.shape[-2], mosaic.shape[-1]
    if max_pixels is not None and n_bands * height * width > max_pixels:
        raise RasterSizeLimitError(
            f"mosaic is {n_bands * height * width} pixels "
            f"(> max_pixels={max_pixels}). Pass a smaller bbox or raise max_pixels."
        )
    return mosaic, out_transform, out_crs


def _bounds_from(transform: Any, width: int, height: int) -> tuple[float, float, float, float]:
    left = float(transform.c)
    top = float(transform.f)
    right = left + float(transform.a) * width
    bottom = top + float(transform.e) * height
    return left, bottom, right, top


def download_assets_windowed(
    items: Sequence[Any],
    assets: Iterable[str],
    dest_dir: Path,
    bbox: tuple[float, float, float, float],
    *,
    max_pixels: int = DEFAULT_MAX_PIXELS,
) -> dict[str, Path]:
    """Windowed download + mosaic of named assets from all covering items."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    wanted = list(assets)
    paths: dict[str, Path] = {}
    for name in wanted:
        pieces: list[tuple[np.ndarray, Any, Any]] = []
        for item in items:
            signed = _sign(item)
            if name not in signed.assets:
                continue
            href = signed.assets[name].href
            try:
                data, transform, crs, _profile = windowed_read(
                    href, bbox, max_pixels=max_pixels
                )
            except RasterDoesNotIntersectError:
                continue
            pieces.append((data, transform, crs))
        if not pieces:
            continue
        mosaic, transform, crs = mosaic_arrays(pieces, max_pixels=max_pixels)
        out = dest_dir / f"{name}.tif"
        write_geotiff(
            mosaic,
            out,
            transform=transform,
            crs=crs,
            nodata=float("nan"),
            band_names=[name],
        )
        paths[name] = out
    if not paths:
        raise FileNotFoundError(f"none of {wanted} could be windowed for bbox={bbox}")
    return paths


def apply_scl_mask(
    stack: np.ndarray,
    scl: np.ndarray,
    nodata: float = float("nan"),
) -> np.ndarray:
    """Mask Sentinel-2 stack where SCL is cloud / shadow / cirrus."""
    mask = np.isin(np.asarray(scl).squeeze(), list(SCL_CLOUD))
    out = np.array(stack, dtype=float, copy=True)
    if out.ndim == 2:
        out[mask] = nodata
    else:
        out[:, mask] = nodata
    return out


def items_cover_bbox(
    items: Sequence[Any],
    bbox: tuple[float, float, float, float],
    *,
    tolerance: float = 1e-4,
) -> bool:
    """True if the union of item bboxes covers ``bbox`` (half-pixel slack)."""
    west, south, east, north = bbox
    if not items:
        return False
    u_w = u_s = u_e = u_n = None
    for item in items:
        ib = getattr(item, "bbox", None) or (item.properties or {}).get("bbox")
        if not ib or len(ib) < 4:
            geom = getattr(item, "geometry", None) or {}
            coords = geom.get("coordinates") if isinstance(geom, dict) else None
            if not coords:
                return False
            continue
        iw, is_, ie, inn = (float(ib[0]), float(ib[1]), float(ib[2]), float(ib[3]))
        u_w = iw if u_w is None else min(u_w, iw)
        u_s = is_ if u_s is None else min(u_s, is_)
        u_e = ie if u_e is None else max(u_e, ie)
        u_n = inn if u_n is None else max(u_n, inn)
    if u_w is None:
        return False
    return (
        u_w <= west + tolerance
        and u_s <= south + tolerance
        and u_e >= east - tolerance
        and u_n >= north - tolerance
    )


def covering_date_items(
    items: Sequence[Any],
    bbox: tuple[float, float, float, float],
) -> list[Any]:
    """Prefer the least-cloudy day whose tiles cover the AOI."""
    if not items:
        return []
    tried: set[str] = set()
    for item in items:
        day = str((item.properties or {}).get("datetime") or "")[:10]
        if not day or day in tried:
            continue
        tried.add(day)
        same = [
            it
            for it in items
            if str((it.properties or {}).get("datetime") or "")[:10] == day
        ]
        if items_cover_bbox(same, bbox):
            return same
    # Fall back to the first day's tiles even if coverage is incomplete.
    best = items[0]
    day = str((best.properties or {}).get("datetime") or "")[:10]
    same = [
        it
        for it in items
        if str((it.properties or {}).get("datetime") or "")[:10] == day
    ]
    return same or [best]


def cache_key(*parts: Any) -> str:
    raw = "|".join(str(p) for p in parts)
    return hashlib.md5(raw.encode()).hexdigest()


def layer_cache_dir(kind: str, *parts: Any) -> Path:
    path = imagery_dir() / kind / cache_key(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path
