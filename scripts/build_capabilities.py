#!/usr/bin/env python3
"""Generate or check docs/source/reference/capabilities.rst from YAML."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_lib import RECIPES_RST, load_catalog, recipe_rst  # noqa: E402

RST_PATH = ROOT / "docs" / "source" / "reference" / "capabilities.rst"


def _recipe_cell(item: dict) -> str:
    if item.get("blocked"):
        return f"blocked: {item['blocked']}"
    if item.get("status") == "adapter-only":
        interop = item.get("interop")
        return f"interop ``{interop}``" if interop else "interop"
    recipe = item.get("recipe")
    if not recipe:
        return "—"
    rst = recipe_rst(item)
    if rst is not None and rst.is_file():
        return f":doc:`/reference/recipes/{recipe}`"
    return f"``{recipe}``"


def render() -> str:
    lines = [
        "Capability catalog",
        "==================",
        "",
        "Generated from ``docs/source/catalog/capabilities.yaml``.",
        "Status is one of ``stable``, ``experimental``, ``adapter-only``,",
        "or ``planned``. ``planned`` items are never public exports.",
        "A ``blocked`` row is a public function that cannot yet ship a",
        "redistributable real-data recipe.",
        "",
        "Do not hand-edit the table. Run ``python scripts/build_capabilities.py``.",
        "",
        "See :doc:`/reference/recipes/index` for the case pages.",
        "",
        ".. list-table::",
        "   :header-rows: 1",
        "   :widths: 32 14 12 18 24",
        "",
        "   * - Function",
        "     - Status",
        "     - Extra",
        "     - Backend",
        "     - Recipe",
    ]
    for item in load_catalog():
        lines.extend(
            [
                f"   * - ``{item['function']}``",
                f"     - {item['status']}",
                f"     - {item['extra']}",
                f"     - {item['backend']}",
                f"     - {_recipe_cell(item)}",
            ]
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = render()
    if args.check:
        current = RST_PATH.read_text(encoding="utf-8") if RST_PATH.exists() else ""
        if current != text:
            print("capabilities.rst is stale; run python scripts/build_capabilities.py")
            return 1
        print("capabilities.rst matches YAML")
        return 0
    RST_PATH.write_text(text, encoding="utf-8")
    print(f"wrote {RST_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
