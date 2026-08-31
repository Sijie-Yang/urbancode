"""Turn a street-view catalog or feature table into a point Layer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from urbancode.city import Layer
from urbancode.images import from_table
from urbancode.provenance import stamp_layer

_LON = ("lon", "longitude", "lng", "x")
_LAT = ("lat", "latitude", "y")
_PATH = ("image_path", "image_uri", "path", "Filename", "filename")


def as_layer(
    frame: Any,
    *,
    name: str = "streetview",
    lon: str | None = None,
    lat: str | None = None,
    crs: str = "EPSG:4326",
) -> Layer:
    """Build a georeferenced point Layer from a comfort/color/catalog table.

    Wraps :func:`urbancode.images.from_table` and sets
    ``view_type="streetview"``. ``frame`` may be a DataFrame or a
    catalog path (``.json`` / ``.csv``).
    """
    if isinstance(frame, (str, Path)):
        layer = from_table(
            frame,
            view_type="streetview",
            lon=lon,
            lat=lat,
            crs=crs,
            name=name,
        )
        return _mark_as_layer(layer)
    if frame is None:
        raise TypeError("as_layer needs a DataFrame or catalog path")
    lon_col = lon or _first_column(frame, _LON)
    lat_col = lat or _first_column(frame, _LAT)
    if not lon_col or not lat_col:
        raise ValueError(
            "streetview.as_layer needs longitude/latitude columns "
            "(lon/lat, longitude/latitude, or x/y)"
        )
    out = frame.copy()
    id_strategy = None
    if "image_id" not in out.columns:
        if "Filename" in out.columns:
            out["image_id"] = out["Filename"].astype(str)
        elif _first_column(out, _PATH):
            id_strategy = "uri_hash"
        else:
            out["image_id"] = [f"image:{i}" for i in range(len(out))]
    layer = from_table(
        out,
        id_column="image_id" if "image_id" in out.columns else None,
        path_column=_first_column(out, _PATH),
        lon=lon_col,
        lat=lat_col,
        view_type="streetview",
        source=_first_scalar(out, "source"),
        license=_first_scalar(out, "license"),
        city_id=_first_scalar(out, "city_id"),
        crs=crs,
        name=name,
        id_strategy=id_strategy,
    )
    return _mark_as_layer(layer)


def _mark_as_layer(layer: Layer) -> Layer:
    layer.source = "urbancode.streetview.as_layer"
    processing = dict((layer.metadata or {}).get("processing") or {})
    processing["op"] = "as_layer"
    processing["wrapped"] = "urbancode.images.from_table"
    layer.metadata["processing"] = processing
    layer.metadata["column"] = (
        "Colorfulness"
        if "Colorfulness" in getattr(layer.data, "columns", [])
        else (
            "visual_comfort"
            if "visual_comfort" in getattr(layer.data, "columns", [])
            else None
        )
    )
    stamp_layer(layer)
    return layer


def _first_column(frame: Any, names: tuple[str, ...]) -> str | None:
    lookup = {str(c).lower(): str(c) for c in frame.columns}
    for name in names:
        if name in lookup:
            return lookup[name]
    return None


def _first_scalar(frame: Any, column: str) -> str | None:
    if column not in getattr(frame, "columns", []):
        return None
    if len(frame) == 0:
        return None
    value = frame[column].iloc[0]
    if value is None:
        return None
    text = str(value)
    return text if text and text != "nan" else None
