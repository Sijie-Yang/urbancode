#!/usr/bin/env python3
"""Discover and run examples/recipes/**/*.py that expose main(out_dir)."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "examples" / "recipes"
DEFAULT_OUT = ROOT / "examples" / "output" / "recipes"


def discover(domain: str | None = None, recipe: str | None = None) -> list[Path]:
    paths = sorted(
        path
        for path in RECIPES.rglob("*.py")
        if path.name != "__init__.py" and not path.name.startswith("_")
    )
    if domain:
        paths = [path for path in paths if path.parent.name == domain]
    if recipe:
        key = recipe.replace(".", "/")
        paths = [
            path
            for path in paths
            if path.stem == recipe
            or path.relative_to(RECIPES).with_suffix("").as_posix() == key
        ]
    return paths


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(
        f"uc_recipe_{path.stem}", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_one(path: Path, out_root: Path) -> dict:
    module = load_module(path)
    if not hasattr(module, "main"):
        raise AttributeError(f"{path} has no main(out_dir)")
    dest = out_root / path.relative_to(RECIPES).with_suffix("")
    dest.mkdir(parents=True, exist_ok=True)
    result = module.main(dest)
    if not isinstance(result, dict):
        raise TypeError(f"{path} main() must return a dict")
    for key in ("figures", "artifacts", "summary"):
        if key not in result:
            raise KeyError(f"{path} return dict missing {key!r}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--domain")
    parser.add_argument("--recipe")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    paths = discover(domain=args.domain, recipe=args.recipe)
    if args.list or not (args.all or args.domain or args.recipe):
        for path in paths:
            print(path.relative_to(RECIPES).with_suffix("").as_posix())
        return 0
    if not paths:
        print("no recipes matched", file=sys.stderr)
        return 1
    for path in paths:
        print(f"running {path.relative_to(ROOT)}")
        out = run_one(path, args.out)
        figures = out.get("figures") or []
        print(f"  figures={len(figures)} summary={out.get('summary')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
