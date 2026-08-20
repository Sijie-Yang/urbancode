#!/usr/bin/env python3
"""Run recipes and copy figures into docs/source/_static."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_lib import FIGURES, analysis_items, figure_path, is_blocked, load_catalog  # noqa: E402
from run_recipes import discover, run_one  # noqa: E402

OUT = ROOT / "examples" / "output" / "docs_examples"


def _copy_figures(result: dict) -> list[Path]:
    copied: list[Path] = []
    for figure in result.get("figures") or []:
        src = Path(figure)
        if not src.is_file():
            continue
        rel = src.name
        dest_dir = FIGURES / "recipes"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / rel
        # Prefer an explicit docs path on the result.
        docs_path = result.get("docs_figures", {}).get(src.name) if isinstance(result.get("docs_figures"), dict) else None
        if docs_path:
            dest = FIGURES / docs_path
            dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied.append(dest)
    return copied


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--domain")
    parser.add_argument("--recipe")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--require-catalog", action="store_true")
    args = parser.parse_args()
    if args.check:
        from check_recipe_figures import catalog_figures, existing_static_figures

        errors = catalog_figures(require=args.require_catalog)
        errors.extend(existing_static_figures())
        if errors:
            print("\n".join(errors))
            return 1
        print("docs example figures ok")
        return 0

    paths = discover(domain=args.domain, recipe=args.recipe)
    if not paths:
        print("no recipes matched", file=sys.stderr)
        return 1
    for path in paths:
        print(f"running {path.relative_to(ROOT)}")
        result = run_one(path, OUT)
        copied = _copy_figures(result)
        for dest in copied:
            print(f"  copied {dest.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
