"""Study area: bbox, CRS, and place metadata. No heavy GIS at import."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


def utm_crs_from_lonlat(lon: float, lat: float) -> str:
    """EPSG code for the UTM zone covering ``(lon, lat)``."""
    zone = int((float(lon) + 180.0) // 6.0) + 1
    zone = min(max(zone, 1), 60)
    epsg = (32600 if float(lat) >= 0 else 32700) + zone
    return f"EPSG:{epsg}"


def _bbox_from_bounds(bounds: Any) -> tuple[float, float, float, float]:
    if bounds is None:
        raise ValueError("geometry has no bounds")
    if len(bounds) != 4:
        raise ValueError("bounds must be (west, south, east, north) or (minx, miny, maxx, maxy)")
    west, south, east, north = (float(v) for v in bounds)
    if east < west or north < south:
        raise ValueError("bbox must be west <= east and south <= north")
    return west, south, east, north


def _is_geographic_crs(crs: Any) -> bool:
    if crs is None:
        return True
    if hasattr(crs, "is_geographic"):
        return bool(crs.is_geographic)
    text = str(crs).upper().replace(" ", "")
    return (
        "EPSG:4326" in text
        or text in {"4326", "OGC:CRS84", "CRS84"}
        or "GEOGCS" in text
    )


def _slug(name: str | None) -> str:
    if not name:
        return "city"
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", str(name).strip()).strip("-").lower()
    return slug or "city"


def _crs_to_str(crs: Any) -> str | None:
    if crs is None:
        return None
    if hasattr(crs, "to_string"):
        return crs.to_string()
    return str(crs)


@dataclass
class StudyArea:
    """Geographic envelope used to build a City and AnalysisUnits."""

    place: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    geographic_crs: str = "EPSG:4326"
    metric_crs: str = ""
    timezone: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    geometry: Any = None
    boundary: Any = None
    city_id: str = ""
    provenance_id: str | None = None

    def __post_init__(self) -> None:
        if self.bbox is not None:
            self.bbox = _bbox_from_bounds(self.bbox)
        if not self.metric_crs and self.bbox is not None:
            west, south, east, north = self.bbox
            self.metric_crs = utm_crs_from_lonlat((west + east) / 2.0, (south + north) / 2.0)
        if not self.city_id:
            self.city_id = _slug(self.place)

    @property
    def projected_crs(self) -> str:
        return self.metric_crs

    @projected_crs.setter
    def projected_crs(self, value: str) -> None:
        self.metric_crs = value

    def to_record(self) -> dict[str, Any]:
        return {
            "city_id": self.city_id,
            "place": self.place,
            "bbox": list(self.bbox) if self.bbox is not None else None,
            "geographic_crs": self.geographic_crs,
            "projected_crs": self.projected_crs,
            "metric_crs": self.metric_crs,
            "timezone": self.timezone,
            "metadata": dict(self.metadata),
            "provenance_id": self.provenance_id,
        }

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> StudyArea:
        bbox = record.get("bbox")
        area = cls(
            place=record.get("place"),
            bbox=tuple(bbox) if bbox else None,
            geographic_crs=str(record.get("geographic_crs") or "EPSG:4326"),
            metric_crs=str(record.get("projected_crs") or record.get("metric_crs") or ""),
            timezone=record.get("timezone"),
            metadata=dict(record.get("metadata") or {}),
            city_id=str(record.get("city_id") or ""),
            provenance_id=record.get("provenance_id"),
        )
        return area

    @classmethod
    def from_bbox(
        cls,
        west: float,
        south: float,
        east: float,
        north: float,
        *,
        place: str | None = None,
        crs: str | None = None,
        geographic_crs: str = "EPSG:4326",
        metric_crs: str | None = None,
        timezone: str | None = None,
        metadata: dict[str, Any] | None = None,
        city_id: str | None = None,
    ) -> StudyArea:
        """Build from ``(west, south, east, north)`` in ``crs`` (default geographic).

        If ``crs`` is projected, the box is reprojected to ``geographic_crs``
        before UTM is derived. Metres are never treated as lon/lat.
        """
        bbox = _bbox_from_bounds((west, south, east, north))
        input_crs = crs or geographic_crs
        if not _is_geographic_crs(input_crs):
            from urbancode.errors import require_extra
            from shapely.geometry import box

            gpd = require_extra("geopandas", "vector")
            frame = gpd.GeoDataFrame(geometry=[box(*bbox)], crs=input_crs)
            geographic = frame.to_crs(geographic_crs)
            geo_bbox = _bbox_from_bounds(geographic.total_bounds)
            return cls(
                place=place,
                bbox=geo_bbox,
                geographic_crs=geographic_crs,
                metric_crs=metric_crs or _crs_to_str(input_crs) or "",
                timezone=timezone,
                metadata=dict(metadata or {}),
                city_id=city_id or "",
                geometry=frame,
                boundary=frame,
            )
        west, south, east, north = bbox
        if abs(west) > 180 or abs(east) > 180 or abs(south) > 90 or abs(north) > 90:
            raise ValueError(
                "bbox looks projected (outside lon/lat range) but crs is "
                f"geographic ({input_crs}). Pass crs= with the projected CRS."
            )
        return cls(
            place=place,
            bbox=bbox,
            geographic_crs=geographic_crs,
            metric_crs=metric_crs or "",
            timezone=timezone,
            metadata=dict(metadata or {}),
            city_id=city_id or "",
        )

    @classmethod
    def from_geometry(
        cls,
        geometry: Any,
        *,
        place: str | None = None,
        geographic_crs: str = "EPSG:4326",
        metric_crs: str | None = None,
        timezone: str | None = None,
        metadata: dict[str, Any] | None = None,
        city_id: str | None = None,
    ) -> StudyArea:
        """Build from Shapely, GeoSeries, GeoDataFrame, or a 4-tuple.

        Inherits CRS from the input. Projected coordinates are reprojected
        to ``geographic_crs`` before UTM is derived. Never treat metres as lon/lat.
        """
        if isinstance(geometry, (tuple, list)) and len(geometry) == 4:
            west, south, east, north = _bbox_from_bounds(geometry)
            if abs(west) > 180 or abs(east) > 180 or abs(south) > 90 or abs(north) > 90:
                raise ValueError(
                    "bounds look projected (outside lon/lat range) but the geometry "
                    "has no CRS. Set a projected CRS before calling from_geometry."
                )
            return cls.from_bbox(
                west,
                south,
                east,
                north,
                place=place,
                geographic_crs=geographic_crs,
                metric_crs=metric_crs,
                timezone=timezone,
                metadata=metadata,
                city_id=city_id,
            )

        src_crs = getattr(geometry, "crs", None)
        if hasattr(geometry, "total_bounds"):
            bounds = geometry.total_bounds
        elif hasattr(geometry, "bounds"):
            bounds = geometry.bounds
        else:
            raise TypeError(
                "geometry must have .bounds / .total_bounds or be a 4-tuple bbox"
            )

        if src_crs is not None and not _is_geographic_crs(src_crs):
            from urbancode.errors import require_extra

            gpd = require_extra("geopandas", "vector")
            if hasattr(geometry, "to_crs"):
                geographic = geometry.to_crs(geographic_crs)
            else:
                geographic = gpd.GeoSeries([geometry], crs=src_crs).to_crs(geographic_crs)
            if hasattr(geographic, "total_bounds"):
                geo_bounds = geographic.total_bounds
            else:
                geo_bounds = geographic.bounds
            west, south, east, north = _bbox_from_bounds(geo_bounds)
            area = cls.from_bbox(
                west,
                south,
                east,
                north,
                place=place,
                geographic_crs=geographic_crs,
                metric_crs=metric_crs or _crs_to_str(src_crs),
                timezone=timezone,
                metadata=metadata,
                city_id=city_id,
            )
            area.geometry = geometry
            area.boundary = geometry if hasattr(geometry, "to_file") else None
            return area

        west, south, east, north = _bbox_from_bounds(bounds)
        if abs(west) > 180 or abs(east) > 180 or abs(south) > 90 or abs(north) > 90:
            raise ValueError(
                "bounds look projected (outside lon/lat range) but the geometry "
                "has no CRS. Set a projected CRS before calling from_geometry."
            )
        area = cls.from_bbox(
            west,
            south,
            east,
            north,
            place=place,
            geographic_crs=_crs_to_str(src_crs) or geographic_crs,
            metric_crs=metric_crs,
            timezone=timezone,
            metadata=metadata,
            city_id=city_id,
        )
        area.geometry = geometry
        if hasattr(geometry, "to_file") or hasattr(geometry, "geometry"):
            area.boundary = geometry
        return area

    @classmethod
    def from_place(
        cls,
        place: str,
        *,
        timezone: str | None = None,
        metadata: dict[str, Any] | None = None,
        city_id: str | None = None,
    ) -> StudyArea:
        """Geocode a place name. Needs geopy (``urbancode[vector]``) or osmnx."""
        from urbancode.geocode import geocode_bbox

        west, south, east, north = geocode_bbox(place)
        return cls.from_bbox(
            west,
            south,
            east,
            north,
            place=place,
            timezone=timezone,
            metadata=metadata,
            city_id=city_id,
        )
