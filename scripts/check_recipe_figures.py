#!/usr/bin/env python3
"""Check committed recipe/workflow/domain figures."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_lib import FIGURES, analysis_items, figure_path, is_blocked, load_catalog  # noqa: E402

MIN_WIDTH = 240
MIN_HEIGHT = 160
STATIC_ROOTS = (
    FIGURES / "recipes",
    FIGURES / "workflows",
    FIGURES / "domains",
)


def is_blank(path: Path) -> bool:
    image = Image.open(path)
    image = image.convert("RGBA")
    extrema = image.getextrema()
    if extrema is None:
        return True
    # All-transparent or a single flat colour.
    if all(channel[0] == channel[1] for channel in extrema) and extrema[3][1] == 0:
        return True
    if image.size[0] * image.size[1] < 16:
        return True
    bands = image.split()
    if all(band.getextrema() == (band.getextrema()[0], band.getextrema()[0]) for band in bands):
        return True
    return False


def check_png(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing {path}"]
    image = Image.open(path)
    width, height = image.size
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        errors.append(f"{path.name}: {width}x{height} below {MIN_WIDTH}x{MIN_HEIGHT}")
    if is_blank(path):
        errors.append(f"{path.name}: blank or fully transparent")
    return errors


def catalog_figures(*, require: bool) -> list[str]:
    errors: list[str] = []
    for item in analysis_items(load_catalog()):
        if is_blocked(item):
            continue
        path = figure_path(item)
        if path is None:
            if require:
                errors.append(f"{item['id']}: no figure")
            continue
        if not path.is_file():
            if require:
                errors.append(f"{item['id']}: missing {path.relative_to(ROOT)}")
            continue
        errors.extend(check_png(path))
    return errors


def existing_static_figures() -> list[str]:
    errors: list[str] = []
    for root in STATIC_ROOTS:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.png")):
            errors.extend(check_png(path))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-catalog",
        action="store_true",
        help="Fail when a non-blocked catalog figure is missing.",
    )
    args = parser.parse_args()
    errors = catalog_figures(require=args.require_catalog)
    errors.extend(existing_static_figures())
    if errors:
        print("\n".join(errors))
        return 1
    print("recipe figures ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
