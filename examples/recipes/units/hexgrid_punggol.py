from __future__ import annotations

from pathlib import Path

from examples.recipes.units._units import run_units


def main(out_dir: str | Path) -> dict:
    return run_units(out_dir)
