"""Human-perception scores from city photos (street view or window view).

Importing this package does not import torch. Model code lives in
``urbancode.perception.backends``.
"""

from __future__ import annotations

from typing import Any

__all__ = ["thermal_affordance"]


def __getattr__(name: str) -> Any:
    if name == "thermal_affordance":
        from urbancode.perception.predict import thermal_affordance

        globals()["thermal_affordance"] = thermal_affordance
        return thermal_affordance
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
