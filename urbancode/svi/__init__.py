"""Deprecated alias of ``urbancode.streetview``. Do not add new APIs here."""

from __future__ import annotations

import warnings
from typing import Any

__all__ = [
    "filename",
    "color",
    "segmentation",
    "object_detection",
    "scene_recognition",
    "comfort",
    "fetch",
]

_WARNED = False


def _warn_once() -> None:
    global _WARNED
    if _WARNED:
        return
    _WARNED = True
    warnings.warn(
        "uc.svi is deprecated; use uc.streetview. "
        "See docs/source/migration/svi-to-streetview.rst",
        DeprecationWarning,
        stacklevel=3,
    )


def __getattr__(name: str) -> Any:
    _warn_once()
    import urbancode.streetview as streetview

    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(streetview, name)
    globals()[name] = value
    return value
