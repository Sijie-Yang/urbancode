"""Weather and thermal comfort. Heavy deps load on first use."""

from __future__ import annotations

from typing import Any

__all__ = ["utci"]


def __getattr__(name: str) -> Any:
    if name == "utci":
        from urbancode.climate.thermal import utci

        globals()["utci"] = utci
        return utci
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
