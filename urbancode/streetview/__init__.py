"""Street-view imagery, features, and deprecated TCIS comfort.

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
    if name in {
        "filename",
        "color",
        "segmentation",
        "object_detection",
        "scene_recognition",
    }:
        from urbancode.streetview import features as feature_mod

        value = getattr(feature_mod, name)
        globals()[name] = value
        return value
    if name == "comfort":
        from urbancode.streetview.perception import comfort

        globals()["comfort"] = comfort
        return comfort
    if name == "fetch":
        from urbancode.streetview.download import fetch

        globals()["fetch"] = fetch
        return fetch
    if name == "as_layer":
        from urbancode.streetview.points import as_layer

        globals()["as_layer"] = as_layer
        return as_layer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
