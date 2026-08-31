"""NDVI from named Sentinel bands, with building outlines."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

DATA = Path(__file__).resolve().parents[1] / "data" / "punggol_pocket"


def main(out_dir: str | Path, *, add_basemap: bool = False) -> dict[str, Path]:
    city = uc.load(DATA)
    ndvi = uc.imagery.ndvi(city["sentinel2"])
    figure = ndvi.plot(
        overlay=city["buildings"],
        title="Punggol, Singapore — NDVI",
        save=Path(out_dir) / "03_ndvi.png",
    )
    del add_basemap
    return {"figure": figure}


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
