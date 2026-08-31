#!/usr/bin/env python3
"""Build research-case figures (TCIS and/or HRIS)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=("tcis", "hris", "all"), default="all")
    parser.add_argument("--mode", choices=("tiny", "case", "full"), default="case")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    if args.case in {"tcis", "all"}:
        from examples.research_cases.thermal_comfort_in_sight import main as run_tcis

        tcis_out = args.out if args.case == "tcis" else str(
            ROOT / "examples" / "output" / "research_cases" / "thermal_comfort_in_sight"
        )
        result = run_tcis(tcis_out, mode=args.mode)
        print(result["summary"])
        for path in result["figures"]:
            print(path)

    if args.case in {"hris", "all"}:
        from examples.research_cases.heat_resilience_in_sight import main as run_hris

        hris_out = args.out or str(
            ROOT / "examples" / "output" / "research_cases" / "heat_resilience_in_sight"
        )
        result = run_hris(hris_out)
        print(result["summary"])
        for path in result["figures"]:
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
