"""Analysis units: a shared spatial frame for indicators."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Any

from urbancode.area import StudyArea, utm_crs_from_lonlat
from urbancode.city import City, Layer
from urbancode.errors import require_extra


def _is_geographic_crs(crs: Any) -> bool:
    if crs is None:
        return False
    if hasattr(crs, "is_geographic"):
        return bool(crs.is_geographic)
    text = str(crs).upper().replace(" ", "")
    return (
        "EPSG:4326" in text
        or text in {"4326", "OGC:CRS84", "CRS84"}
        or "GEOGCS" in text
    )


def _city_bbox(city: City) -> tuple[float, float, float, float]:
    area = getattr(city, "study_area", None)
    if area is not None and getattr(area, "bbox", None) is not None:
        return tuple(float(v) for v in area.bbox)  # type: ignore[return-value]
    bbox = (city.metadata or {}).get("bbox")
    if bbox and len(bbox) == 4:
        return float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
    boundary = city.boundary
    if boundary is not None and hasattr(boundary, "total_bounds"):
        west, south, east, north = boundary.total_bounds
        return float(west), float(south), float(east), float(north)
    raise ValueError(
        "cannot build a grid: City has no study_area.bbox, metadata['bbox'], or boundary"
    )


def _metric_crs_for(city: City, metric_crs: str | None) -> str:
    if metric_crs:
        if _is_geographic_crs(metric_crs):
            raise ValueError(
                "grid cell_size is metres; pass a projected metric_crs, not a geographic CRS"
            )
        return metric_crs
    area = getattr(city, "study_area", None)
    if area is not None and getattr(area, "metric_crs", None):
        if _is_geographic_crs(area.metric_crs):
            raise ValueError(
                "study_area.metric_crs is geographic; set a projected CRS before building a grid"
            )
        return str(area.metric_crs)
    west, south, east, north = _city_bbox(city)
    return utm_crs_from_lonlat((west + east) / 2.0, (south + north) / 2.0)


def _city_id(city: City | str | None) -> str:
    if isinstance(city, str):
        return city
    if city is None:
        return "city"
    area = getattr(city, "study_area", None)
    if area is not None and getattr(area, "city_id", None):
        return str(area.city_id)
    return str(city.place or city.metadata.get("city_id") or "city")


def _study_area_id(city: City) -> str:
    area = getattr(city, "study_area", None)
    if area is not None and getattr(area, "city_id", None):
        return str(area.city_id)
    return _city_id(city)


def _format_size(cell_size: float) -> str:
    text = f"{float(cell_size):.6f}".rstrip("0").rstrip(".")
    return text or "0"


def validate_units(frame: Any) -> None:
    """Raise if unit_id / geometry / CRS are not usable."""
    if frame is None or not hasattr(frame, "geometry"):
        raise ValueError("AnalysisUnits.frame must be a GeoDataFrame")
    if getattr(frame, "crs", None) is None:
        raise ValueError("AnalysisUnits need a CRS")
    if "unit_id" not in frame.columns:
        raise ValueError("AnalysisUnits need a unit_id column")
    ids = [str(v) for v in frame["unit_id"].tolist()]
    if any(not i or i == "nan" for i in ids):
        raise ValueError("unit_id must be non-empty")
    if len(ids) != len(set(ids)):
        raise ValueError("unit_id values must be unique")
    geoms = frame.geometry
    if geoms.isna().any() or getattr(geoms, "is_empty", geoms).any():
        raise ValueError("every unit must have a non-empty geometry")
    if hasattr(geoms, "is_valid") and not bool(geoms.is_valid.all()):
        raise ValueError("every unit must have a valid geometry")


@dataclass
class AnalysisUnits:
    """Polygons with a stable ``unit_id`` in a metric CRS."""

    frame: Any
    city_id: str
    kind: str = "grid"
    cell_size: float | None = None
    crs: str = ""
    metric_crs: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_units(self.frame)

    @property
    def unit_ids(self) -> list[str]:
        return [str(v) for v in self.frame["unit_id"].tolist()]


def grid(
    city: City,
    cell_size: float = 250,
    *,
    metric_crs: str | None = None,
    geographic_crs: str = "EPSG:4326",
) -> AnalysisUnits:
    """Square grid in metres. IDs use a world origin, not the pocket min-corner."""
    if cell_size <= 0:
        raise ValueError("cell_size must be positive metres")
    gpd = require_extra("geopandas", "vector")
    from shapely.geometry import box

    target_crs = _metric_crs_for(city, metric_crs)
    west, south, east, north = _city_bbox(city)
    envelope = gpd.GeoDataFrame(
        geometry=[box(west, south, east, north)],
        crs=geographic_crs,
    ).to_crs(target_crs)
    minx, miny, maxx, maxy = envelope.total_bounds
    size = float(cell_size)
    col0 = math.floor(minx / size)
    col1 = math.floor((maxx - 1e-9) / size)
    row0 = math.floor(miny / size)
    row1 = math.floor((maxy - 1e-9) / size)
    size_key = _format_size(size)
    crs_key = str(target_crs).replace(" ", "")
    geometries = []
    unit_ids = []
    cols = []
    rows = []
    for col in range(col0, col1 + 1):
        for row in range(row0, row1 + 1):
            x = col * size
            y = row * size
            geometries.append(box(x, y, x + size, y + size))
            unit_ids.append(f"grid:{crs_key}:{size_key}:{col}:{row}")
            cols.append(col)
            rows.append(row)
    if not geometries:
        raise ValueError("grid is empty; check bbox and cell_size")
    area_id = _study_area_id(city)
    frame = gpd.GeoDataFrame(
        {
            "unit_id": unit_ids,
            "unit_type": "grid",
            "resolution": size,
            "crs": str(target_crs),
            "study_area_id": area_id,
            "col": cols,
            "row": rows,
        },
        geometry=geometries,
        crs=target_crs,
    )
    return AnalysisUnits(
        frame=frame,
        city_id=_city_id(city),
        kind="grid",
        cell_size=size,
        crs=str(target_crs),
        metric_crs=str(target_crs),
        metadata={
            "geographic_crs": geographic_crs,
            "origin": [0.0, 0.0],
            "scheme": "grid.v1",
            "resolution": size,
        },
    )


def hexgrid(
    city: City,
    cell_size: float = 250,
    *,
    metric_crs: str | None = None,
    geographic_crs: str = "EPSG:4326",
) -> AnalysisUnits:
    """Pointy-top hexagons. ``cell_size`` is the centre-to-vertex radius in metres."""
    if cell_size <= 0:
        raise ValueError("cell_size must be positive metres")
    gpd = require_extra("geopandas", "vector")
    from shapely.geometry import box

    target_crs = _metric_crs_for(city, metric_crs)
    west, south, east, north = _city_bbox(city)
    envelope = gpd.GeoDataFrame(
        geometry=[box(west, south, east, north)],
        crs=geographic_crs,
    ).to_crs(target_crs)
    minx, miny, maxx, maxy = envelope.total_bounds
    radius = float(cell_size)
    w = math.sqrt(3.0) * radius
    h = 1.5 * radius
    q0 = math.floor(minx / w) - 1
    q1 = math.floor(maxx / w) + 1
    r0 = math.floor(miny / h) - 1
    r1 = math.floor(maxy / h) + 1
    size_key = _format_size(radius)
    crs_key = str(target_crs).replace(" ", "")
    area_poly = envelope.geometry.iloc[0]
    geometries = []
    unit_ids = []
    qs = []
    rs = []
    for q in range(q0, q1 + 1):
        for r in range(r0, r1 + 1):
            cx = q * w + (r % 2) * (w / 2.0)
            cy = r * h
            hex_poly = _hexagon(cx, cy, radius)
            if not hex_poly.intersects(area_poly):
                continue
            geometries.append(hex_poly)
            unit_ids.append(f"hex:{crs_key}:{size_key}:{q}:{r}")
            qs.append(q)
            rs.append(r)
    if not geometries:
        raise ValueError("hexgrid is empty; check bbox and cell_size")
    area_id = _study_area_id(city)
    frame = gpd.GeoDataFrame(
        {
            "unit_id": unit_ids,
            "unit_type": "hexgrid",
            "resolution": radius,
            "crs": str(target_crs),
            "study_area_id": area_id,
            "q": qs,
            "r": rs,
        },
        geometry=geometries,
        crs=target_crs,
    )
    return AnalysisUnits(
        frame=frame,
        city_id=_city_id(city),
        kind="hexgrid",
        cell_size=radius,
        crs=str(target_crs),
        metric_crs=str(target_crs),
        metadata={
            "geographic_crs": geographic_crs,
            "origin": [0.0, 0.0],
            "scheme": "hex.v1",
            "resolution": radius,
        },
    )


def _hexagon(cx: float, cy: float, radius: float):
    from shapely.geometry import Polygon

    verts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        verts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return Polygon(verts)


def from_layer(
    layer: Layer | Any,
    *,
    id_column: str | None = None,
    city_id: str = "city",
    metric_crs: str | None = None,
    study_area: StudyArea | None = None,
) -> AnalysisUnits:
    """Use existing polygons as units. Reprojects geographic frames."""
    gpd = require_extra("geopandas", "vector")
    frame = layer.data if isinstance(layer, Layer) else layer
    if frame is None or not hasattr(frame, "geometry"):
        raise TypeError("from_layer needs a vector Layer or GeoDataFrame")
    out = frame.copy()
    src_crs = getattr(out, "crs", None)
    target = metric_crs
    if target is None and study_area is not None and study_area.metric_crs:
        target = study_area.metric_crs
    if target is None:
        if src_crs is not None and not _is_geographic_crs(src_crs):
            target = str(src_crs)
        else:
            raise ValueError(
                "from_layer on a geographic CRS needs metric_crs= or a StudyArea "
                "with projected_crs (distance and area units are metres)"
            )
    if _is_geographic_crs(target):
        raise ValueError("metric_crs must be projected, not geographic")
    if src_crs is not None and str(src_crs) != str(target):
        out = out.to_crs(target)
    elif src_crs is None:
        out = out.set_crs(target)
    out = out.copy()
    if id_column and id_column in out.columns:
        out["unit_id"] = out[id_column].astype(str)
    elif "unit_id" not in out.columns:
        out["unit_id"] = [_geometry_id(geom) for geom in out.geometry]
        if out["unit_id"].duplicated().any():
            raise ValueError(
                "from_layer found duplicate geometries; refuse to invent row suffixes"
            )
    else:
        out["unit_id"] = out["unit_id"].astype(str)
    if "unit_type" not in out.columns:
        out["unit_type"] = "from_layer"
    if "resolution" not in out.columns:
        out["resolution"] = float("nan")
    out["crs"] = str(target)
    out["study_area_id"] = (
        study_area.city_id if study_area is not None else city_id
    )
    name = layer.name if isinstance(layer, Layer) else "layer"
    return AnalysisUnits(
        frame=out,
        city_id=city_id,
        kind="from_layer",
        crs=str(target),
        metric_crs=str(target),
        metadata={
            "parent": name,
            "scheme": "from_layer.v1",
            "fingerprint": GEOM_FINGERPRINT_SCHEME,
            "fingerprint_crs": str(target),
            "fingerprint_precision": GEOM_FINGERPRINT_PRECISION,
        },
    )


GEOM_FINGERPRINT_SCHEME = "geom.v1"
GEOM_FINGERPRINT_PRECISION = 0.001


def _geometry_id(geom: Any) -> str:
    if geom is None or getattr(geom, "is_empty", False):
        raise ValueError("cannot fingerprint an empty geometry")
    canonical = _canonical_geometry(geom, GEOM_FINGERPRINT_PRECISION)
    digest = hashlib.sha256(bytes(canonical.wkb)).hexdigest()[:16]
    return f"geom:v1:{digest}"


def _canonical_geometry(geom: Any, precision: float):
    from shapely import normalize, set_precision
    from shapely.geometry import MultiPolygon
    from shapely.ops import orient

    rounded = set_precision(geom, precision)
    if rounded is None or getattr(rounded, "is_empty", False):
        raise ValueError("cannot fingerprint an empty geometry")
    oriented = orient(rounded, sign=1.0)
    if oriented.geom_type == "MultiPolygon":
        parts = sorted(
            oriented.geoms,
            key=lambda part: (
                round(part.bounds[0], 6),
                round(part.bounds[1], 6),
                bytes(part.wkb),
            ),
        )
        oriented = MultiPolygon(parts)
    return normalize(oriented)
