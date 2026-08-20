"""Discrete, geolocated city-photo observations.

This is not satellite imagery (``uc.imagery``) and not street-view
acquisition (``uc.streetview``). Window-view photos use
``view_type="windowview"`` here; they do not belong in streetview.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable

from urbancode.city import Layer
from urbancode.errors import require_extra
from urbancode.provenance import stamp_layer

__all__ = ["from_table"]

VIEW_TYPES = ("streetview", "windowview", "ground_photo")
ID_STRATEGIES = ("uri_hash", "checksum")

_PATH_COLUMNS = ("image_path", "image_uri", "path", "Filename", "filename")
_LON = ("lon", "longitude", "lng", "x")
_LAT = ("lat", "latitude", "y")
_CAPTURED = ("captured_at", "capture_time", "captured_on")
_QUALITY = ("location_quality", "location_accuracy")


def from_table(
    frame: Any,
    *,
    id_column: str | None = "image_id",
    path_column: str | None = None,
    lon: str | None = None,
    lat: str | None = None,
    view_type: str,
    source: str | None = None,
    license: str | None = None,
    city_id: str | None = None,
    captured_at: str | None = None,
    location_quality: str | None = None,
    crs: str = "EPSG:4326",
    name: str = "images",
    id_strategy: str | None = None,
    image_root: str | Path | None = None,
) -> Layer:
    """Build a geolocated image-observation Layer from a table.

    Research cases should pass an explicit ``image_id``. Automatic IDs
    are allowed only with ``id_strategy="uri_hash"`` or ``"checksum"``.

    ``image_root`` resolves relative paths at runtime. Catalogs should
    store ``relative_path``; do not persist machine-specific absolute
    roots in exported predictions or docs.
    """
    if frame is None:
        raise TypeError("images.from_table needs a DataFrame")
    if view_type not in VIEW_TYPES:
        raise ValueError(
            f"view_type must be one of {VIEW_TYPES}; got {view_type!r}"
        )
    if id_strategy is not None and id_strategy not in ID_STRATEGIES:
        raise ValueError(
            f"id_strategy must be one of {ID_STRATEGIES}; got {id_strategy!r}"
        )

    out = frame.copy()
    path_col = path_column or _first_column(out, _PATH_COLUMNS)
    if path_col is None:
        if (id_column and id_column in out.columns) or "image_id" in out.columns:
            key = id_column if id_column and id_column in out.columns else "image_id"
            out["image_uri"] = out[key].astype(str)
            path_col = "image_uri"
        else:
            raise ValueError(
                "images.from_table needs an image path/URI column "
                "(image_path, image_uri, path, or Filename)"
            )
    if path_col != "image_path" and "image_path" not in out.columns:
        out["image_path"] = out[path_col].astype(str)
    if "relative_path" not in out.columns:
        out["relative_path"] = [
            _as_relative_path(value) for value in out["image_path"]
        ]
    else:
        out["relative_path"] = [
            str(value).replace("\\", "/") for value in out["relative_path"]
        ]
    if image_root is not None:
        root = Path(image_root)
        out["image_path"] = [
            _resolve_under_root(rel, current, root)
            for rel, current in zip(out["relative_path"], out["image_path"])
        ]
    if "image_uri" not in out.columns:
        out["image_uri"] = out["image_path"].astype(str)

    if id_column and id_column in out.columns:
        out["image_id"] = out[id_column].astype(str)
    elif id_strategy:
        out["image_id"] = [
            _auto_image_id(value, id_strategy) for value in out["image_path"]
        ]
    else:
        raise ValueError(
            "images.from_table needs an explicit image_id column. "
            "Pass id_column= or id_strategy='uri_hash'/'checksum'. "
            "Geometry-only IDs are not allowed: one location can have "
            "several photos."
        )

    ids = list(out["image_id"].astype(str))
    if len(ids) != len(set(ids)):
        raise ValueError("image_id values must be unique")

    out["view_type"] = view_type
    out["city_id"] = _fill(out, "city_id", city_id)
    out["source"] = _fill(out, "source", source)
    out["license"] = _fill(out, "license", license)
    captured_col = _first_column(out, _CAPTURED)
    out["captured_at"] = (
        out[captured_col] if captured_col else _fill(out, "captured_at", captured_at)
    )
    quality_col = _first_column(out, _QUALITY)
    out["location_quality"] = (
        out[quality_col]
        if quality_col
        else _fill(out, "location_quality", location_quality)
    )

    lon_col = lon or _first_column(out, _LON)
    lat_col = lat or _first_column(out, _LAT)
    has_coords = bool(lon_col and lat_col)
    if has_coords:
        gpd = require_extra("geopandas", "vector")
        data = gpd.GeoDataFrame(
            out,
            geometry=gpd.points_from_xy(out[lon_col], out[lat_col]),
            crs=crs,
        )
        kind = "vector"
        resolved_crs = crs
    else:
        data = out
        kind = "table"
        resolved_crs = None

    layer = Layer(
        name=name,
        kind=kind,
        data=data,
        crs=resolved_crs,
        source="urbancode.images.from_table",
        metadata={
            "processing": {
                "op": "from_table",
                "view_type": view_type,
                "id_strategy": id_strategy,
                "image_root_provided": image_root is not None,
            },
            "view_type": view_type,
            "n_images": int(len(out)),
            "location_quality": _first_value(out["location_quality"]),
            "license": _first_value(out["license"]),
            "id_strategy": id_strategy,
            "image_root_provided": image_root is not None,
        },
    )
    stamp_layer(layer)
    return layer


def _auto_image_id(path_or_uri: Any, strategy: str) -> str:
    text = str(path_or_uri)
    if strategy == "uri_hash":
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        return f"img:{digest}"
    path = Path(text)
    if not path.is_file():
        raise FileNotFoundError(
            f"id_strategy='checksum' needs a readable file; missing {text}"
        )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    return f"img:{digest}"


def _as_relative_path(value: Any) -> str:
    text = str(value).replace("\\", "/")
    path = Path(text)
    if path.is_absolute():
        return path.name
    return text.lstrip("./")


def _resolve_under_root(relative: Any, current: Any, root: Path) -> str:
    current_path = Path(str(current))
    if current_path.is_absolute():
        return str(current_path)
    return str(root / str(relative).replace("\\", "/"))


def _fill(frame: Any, column: str, value: Any) -> Any:
    if value is not None and hasattr(value, "iloc"):
        if len(value) != len(frame):
            raise ValueError(
                f"{column} series length {len(value)} != table length {len(frame)}"
            )
        return list(value)
    if isinstance(value, (list, tuple)):
        if len(value) != len(frame):
            raise ValueError(
                f"{column} list length {len(value)} != table length {len(frame)}"
            )
        return list(value)
    if column in frame.columns and value is None:
        return frame[column]
    if value is None:
        return [None] * len(frame)
    return [value] * len(frame)


def _first_column(frame: Any, names: Iterable[str]) -> str | None:
    lookup = {str(c).lower(): str(c) for c in frame.columns}
    for name in names:
        if name.lower() in lookup:
            return lookup[name.lower()]
    return None


def _first_value(series: Any) -> Any:
    if series is None or len(series) == 0:
        return None
    return series.iloc[0]
