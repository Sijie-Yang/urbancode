#!/usr/bin/env python3
"""Build Thermal Comfort in Sight research-case figures."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("tiny", "case", "full"), default="case")
    parser.add_argument(
        "--out",
        default=str(ROOT / "examples" / "output" / "research_cases" / "thermal_comfort_in_sight"),
    )
    args = parser.parse_args()
    from examples.research_cases.thermal_comfort_in_sight import main as run

    result = run(args.out, mode=args.mode)
    print(result["summary"])
    for path in result["figures"]:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
