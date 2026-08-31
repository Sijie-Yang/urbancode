"""Extras / capability probe. Not a re-export of third-party modules."""

from __future__ import annotations

import importlib
import importlib.util
from typing import Any

from urbancode.errors import require_extra

# name -> (import module, urbancode extra)
_BACKENDS: dict[str, tuple[str, str]] = {
    "geopandas": ("geopandas", "vector"),
    "shapely": ("shapely", "vector"),
    "pyproj": ("pyproj", "vector"),
    "osmnx": ("osmnx", "network"),
    "networkx": ("networkx", "network"),
    "momepy": ("momepy", "network"),
    "rasterio": ("rasterio", "imagery"),
    "rioxarray": ("rioxarray", "imagery"),
    "xarray": ("xarray", "imagery"),
    "pythermalcomfort": ("pythermalcomfort", "climate"),
    "zensvi": ("zensvi", "svi"),
    "streetlevel": ("streetlevel", "svi"),
    "torch": ("torch", "svi"),
    "matplotlib": ("matplotlib", "viz"),
    "city2graph": ("city2graph", "graph"),
}


def available() -> dict[str, bool]:
    """Return whether each known backend module can be imported."""
    found: dict[str, bool] = {}
    for name, (module, _extra) in _BACKENDS.items():
        found[name] = importlib.util.find_spec(module) is not None
    return found


def info(name: str) -> dict[str, Any]:
    """Describe one backend: module, extra, and whether it is installed."""
    if name not in _BACKENDS:
        known = ", ".join(sorted(_BACKENDS))
        raise KeyError(f"unknown backend {name!r}; known: {known}")
    module, extra = _BACKENDS[name]
    installed = importlib.util.find_spec(module) is not None
    return {
        "name": name,
        "module": module,
        "extra": extra,
        "installed": installed,
        "install": f'pip install "urbancode[{extra}]"',
    }


def status() -> dict[str, dict[str, Any]]:
    """Return info() for every registered backend."""
    return {name: info(name) for name in _BACKENDS}


def explain(name: str) -> dict[str, Any]:
    """Like ``info`` plus installed version and a one-line capability note."""
    detail = info(name)
    module, extra = _BACKENDS[name]
    version = None
    error = None
    if detail["installed"]:
        try:
            loaded = importlib.import_module(module)
            version = getattr(loaded, "__version__", None)
        except Exception as exc:
            error = str(exc)
            detail["installed"] = False
    detail["version"] = version
    detail["import_error"] = error
    detail["capability"] = extra
    return detail


def require(name: str) -> Any:
    """Import a backend module or raise ``MissingExtraError``."""
    if name not in _BACKENDS:
        known = ", ".join(sorted(_BACKENDS))
        raise KeyError(f"unknown backend {name!r}; known: {known}")
    module, extra = _BACKENDS[name]
    return require_extra(module, extra)
