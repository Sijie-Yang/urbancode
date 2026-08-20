from __future__ import annotations

from pathlib import Path

from examples.recipes.imagery._terrain import run_terrain


def main(out_dir: str | Path) -> dict:
    return run_terrain(out_dir)
