"""Render offline gallery figures into docs/source/_static/gallery.

Read the Docs does not run this script. Commit the PNGs after a local run.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    ROOT / "examples" / "offline" / "01_streets_buildings.py",
    ROOT / "examples" / "offline" / "02_parks_pois.py",
    ROOT / "examples" / "offline" / "03_ndvi_map.py",
    ROOT / "examples" / "offline" / "04_terrain_hillshade.py",
    ROOT / "examples" / "offline" / "05_zonal_ndvi.py",
    ROOT / "examples" / "offline" / "06_access_radius.py",
    ROOT / "examples" / "offline" / "07_streetview_results.py",
]


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(output: str | Path | None = None) -> dict[str, Path]:
    out_dir = Path(output) if output else ROOT / "docs" / "source" / "_static" / "gallery"
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for path in SCRIPTS:
        module = _load(path)
        result = module.main(out_dir, add_basemap=False)
        written[path.stem] = result["figure"]
        print(f"{path.name} -> {result['figure']}")
    tutorial = _load(ROOT / "scripts" / "build_tutorials.py")
    written.update(tutorial.main(ROOT / "docs" / "source" / "_static" / "tutorials"))
    return written


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(ROOT / "docs" / "source" / "_static" / "gallery"),
        help="Directory for PNG outputs",
    )
    args = parser.parse_args()
    main(args.output)
