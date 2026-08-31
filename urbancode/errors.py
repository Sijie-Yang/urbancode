"""Shared error helpers for optional extras."""

from __future__ import annotations

import importlib
from typing import Any


class MissingExtraError(ImportError):
    """Raised when an optional extra is required but not installed."""


class CityIntegrityError(ValueError):
    """Raised when a City directory is unsafe or fails verification."""


class RasterDoesNotIntersectError(ValueError):
    """Raised when a request bbox does not intersect a raster."""


class RasterSizeLimitError(ValueError):
    """Raised when a window or mosaic exceeds ``max_pixels``."""


def require_extra(module: str, extra: str) -> Any:
    """Import ``module`` or raise an install hint for ``urbancode[extra]``."""
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        raise MissingExtraError(
            f"{module} is required for this feature. "
            f'Install with: pip install "urbancode[{extra}]"'
        ) from exc
