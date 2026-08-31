"""Download street-view imagery into a City. Needs urbancode[download]."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from urbancode.cache import downloads_dir
from urbancode.city import City
from urbancode.errors import require_extra

_ZENSVI_SOURCES = {
    "mapillary": "MLYDownloader",
    "kartaview": "KVDownloader",
    "amsterdam": "AMSDownloader",
}
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
_UNOFFICIAL = frozenset({"google"})


def fetch(
    place: str | None = None,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    source: str = "mapillary",
    out: str | Path | None = None,
    api_key: str | None = None,
    allow_unofficial: bool = False,
    max_images: int | None = None,
) -> City:
    """Download street-level photos and return a :class:`~urbancode.city.City`.

    ``source`` is ``mapillary`` (ZenSVI, API key required), ``kartaview``,
    ``amsterdam``, or ``google`` (streetlevel internal API; experimental).
    Unofficial Google download is off until ``allow_unofficial=True``.

    Pass ``lat`` / ``lon``, ``bbox=(west, south, east, north)``, or a
    geocodable ``place``. Need ``urbancode[download]``.
    """
    source = str(source).lower().strip()
    if source in _UNOFFICIAL and not allow_unofficial:
        raise ValueError(
            "source='google' uses streetlevel internal APIs (experimental, "
            "may break or violate provider terms). Pass allow_unofficial=True "
            "to opt in, or use source='mapillary' / 'kartaview'."
        )
    if source == "mapillary" and not api_key:
        raise ValueError(
            "source='mapillary' requires api_key=... "
            "(register at https://www.mapillary.com/developer)"
        )
    if source not in _ZENSVI_SOURCES and source not in _UNOFFICIAL:
        raise ValueError(
            f"unknown SVI source {source!r}; use "
            "'mapillary', 'kartaview', 'amsterdam', or 'google'"
        )

    lat, lon = _resolve_point(place=place, bbox=bbox, lat=lat, lon=lon)
    dest = Path(out) if out else downloads_dir() / "svi" / source
    dest.mkdir(parents=True, exist_ok=True)

    if source in _ZENSVI_SOURCES:
        _zensvi_download(
            dest,
            source=source,
            lat=lat,
            lon=lon,
            place=place,
            api_key=api_key,
        )
    else:
        _streetlevel_google(dest, lat=lat, lon=lon)

    paths = _list_images(dest)
    if max_images is not None:
        paths = paths[: max(0, int(max_images))]
    if not paths:
        raise ValueError(f"no street-view images landed in {dest}")

    index = pd.DataFrame(
        {
            "path": [str(p) for p in paths],
            "source": source,
            "lat": lat,
            "lon": lon,
            "place": place,
        }
    )
    city = City(
        place=place,
        metadata={
            "source": source,
            "backend": "zensvi" if source in _ZENSVI_SOURCES else "streetlevel",
            "bbox": list(bbox) if bbox else None,
        },
    )
    processing = {
        "op": "svi_fetch",
        "source": source,
        "backend": city.metadata["backend"],
        "allow_unofficial": bool(allow_unofficial),
        "queried_at": datetime.now(timezone.utc).isoformat(),
    }
    city.add_layer(
        "streetview",
        None,
        kind="images",
        path=str(paths[0]),
        source=source,
        metadata={"processing": processing, "directory": str(dest)},
    )
    city.add_layer(
        "svi_index",
        index,
        kind="table",
        source=source,
        metadata={"processing": processing, "column": "path", "parent": "streetview"},
    )
    return city


def _resolve_point(
    *,
    place: str | None,
    bbox: tuple[float, float, float, float] | None,
    lat: float | None,
    lon: float | None,
) -> tuple[float, float]:
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    if bbox is not None:
        west, south, east, north = (float(v) for v in bbox)
        return (south + north) / 2.0, (west + east) / 2.0
    if place:
        from urbancode.geocode import geocode_bbox

        west, south, east, north = geocode_bbox(place)
        return (south + north) / 2.0, (west + east) / 2.0
    raise ValueError("svi.fetch needs place, bbox, or lat/lon")


def _zensvi_download(
    out_dir: Path,
    *,
    source: str,
    lat: float,
    lon: float,
    place: str | None,
    api_key: str | None,
) -> None:
    require_extra("zensvi", "svi")
    from zensvi.download import AMSDownloader, KVDownloader, MLYDownloader

    cls = {"mapillary": MLYDownloader, "kartaview": KVDownloader, "amsterdam": AMSDownloader}[
        source
    ]
    kwargs: dict[str, Any] = {}
    if source == "mapillary":
        kwargs["mly_api_key"] = api_key
    downloader = cls(**kwargs)
    call: dict[str, Any] = {"lat": lat, "lon": lon}
    if place:
        call["input_place_name"] = place
    downloader.download_svi(str(out_dir), **call)


def _streetlevel_google(out_dir: Path, *, lat: float, lon: float) -> None:
    streetview = require_extra("streetlevel.streetview", "svi")
    pano = streetview.find_panorama(lat, lon)
    if pano is None:
        raise ValueError(f"no Google panorama near lat={lat}, lon={lon}")
    dest = out_dir / f"{getattr(pano, 'id', 'pano')}.jpg"
    streetview.download_panorama(pano, str(dest))


def _list_images(directory: Path) -> list[Path]:
    found: list[Path] = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.suffix.lower() in _IMAGE_SUFFIXES:
            found.append(path)
    return found
