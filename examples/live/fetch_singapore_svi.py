"""Live SVI rebuild / gap-fill. Not used for the existing 92,233 store.

This script is for a new dataset or missing tiles. It is not in default
CI. API keys come from the environment only.

    MAPILLARY_TOKEN=... python examples/live/fetch_singapore_svi.py
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import urbancode as uc


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--place", default="Singapore")
    parser.add_argument("--source", default="mapillary")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-images", type=int, default=None)
    args = parser.parse_args(argv)
    token = os.environ.get("MAPILLARY_TOKEN") or os.environ.get("MAPILLARY_API_KEY")
    if args.source == "mapillary" and not token:
        raise SystemExit("MAPILLARY_TOKEN must be set in the environment")
    uc.svi.fetch(
        place=args.place,
        source=args.source,
        out=args.output_dir,
        api_key=token,
        max_images=args.max_images,
    )


if __name__ == "__main__":
    main()
