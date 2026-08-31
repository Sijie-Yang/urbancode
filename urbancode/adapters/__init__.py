"""Lazy re-exports of upstream libraries. Interop, not UrbanCode metrics.

``uc.adapters.osmnx`` is ``osmnx``. Missing extras raise
``MissingExtraError`` with an install hint.
"""

from __future__ import annotations

from typing import Any

from urbancode.errors import require_extra

# name -> (import module, urbancode extra)
_ADAPTERS: dict[str, tuple[str, str]] = {
    "osmnx": ("osmnx", "network"),
    "momepy": ("momepy", "network"),
    "networkx": ("networkx", "network"),
    "geopandas": ("geopandas", "vector"),
    "shapely": ("shapely", "vector"),
    "zensvi": ("zensvi", "svi"),
    "streetlevel": ("streetlevel", "svi"),
    "city2graph": ("city2graph", "graph"),
    "pythermalcomfort": ("pythermalcomfort", "climate"),
}

__all__ = list(_ADAPTERS)


def __getattr__(name: str) -> Any:
    if name not in _ADAPTERS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module, extra = _ADAPTERS[name]
    value = require_extra(module, extra)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_ADAPTERS))
