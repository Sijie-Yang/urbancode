"""Street-view imagery (SVI): catalogs, features, fetch, and deprecated comfort.

This is the official public namespace. ``uc.streetview`` is a
compatibility alias of the same implementation.

Prefer ``uc.perception.thermal_affordance`` for Layer-returning scores.
Heavy deps load on first use.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "filename",
    "color",
    "segmentation",
    "object_detection",
    "scene_recognition",
    "comfort",
    "fetch",
    "as_layer",
]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import urbancode.streetview as streetview

    value = getattr(streetview, name)
    globals()[name] = value
    return value
