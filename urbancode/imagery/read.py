"""Read a local GeoTIFF into a Layer with raster metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from urbancode.city import Layer
from urbancode.errors import require_extra


def read(path: str | Path, name: str | None = None) -> Layer:
    """Open a local GeoTIFF. Does not download anything.

    Returns a :class:`~urbancode.city.Layer` whose ``data`` is a rioxarray
    DataArray and whose ``metadata`` records CRS, bounds, resolution, nodata,
    and band names.
    """
    require_extra("rasterio", "imagery")
    rxr = require_extra("rioxarray", "imagery")
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    da = rxr.open_rasterio(file_path, masked=True)
    metadata = raster_metadata(da, source="local", path=str(file_path))
    return Layer(
        name=name or file_path.stem,
        kind="raster",
        data=da,
        path=str(file_path),
        crs=metadata.get("crs"),
        source="local",
        metadata=metadata,
    )


def raster_metadata(da: Any, *, source: str, path: str | None = None) -> dict[str, Any]:
    """Collect CRS / bounds / resolution / nodata / bands from a DataArray."""
    rio = getattr(da, "rio", None)
    crs = None
    bounds = None
    resolution = None
    nodata = None
    if rio is not None:
        crs = str(rio.crs) if rio.crs is not None else None
        try:
            b = rio.bounds()
            bounds = [float(b.left), float(b.bottom), float(b.right), float(b.top)]
        except Exception:
            bounds = None
        try:
            res = rio.resolution()
            resolution = [abs(float(res[0])), abs(float(res[1]))]
        except Exception:
            resolution = None
        nodata = rio.nodata
    band_names: list[str] = []
    if path:
        try:
            import rasterio

            with rasterio.open(path) as src:
                descs = [str(d) for d in src.descriptions if d]
            if descs:
                band_names = descs
        except Exception:
            band_names = []
    if not band_names and "band" in getattr(da, "coords", {}):
        band_names = [str(v) for v in da.coords["band"].values]
    elif not band_names and hasattr(da, "long_name"):
        band_names = [str(da.long_name)]
    return {
        "crs": crs,
        "bounds": bounds,
        "resolution": resolution,
        "nodata": nodata,
        "bands": band_names,
        "datetime": None,
        "source": source,
        "license": None,
        "path": path,
    }
