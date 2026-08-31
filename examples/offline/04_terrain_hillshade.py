"""Hillshade with slope overlay for the Copernicus DEM."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

DATA = Path(__file__).resolve().parents[1] / "data" / "real" / "punggol"


def main(out_dir: str | Path, *, add_basemap: bool = False) -> dict[str, Path]:
    city = uc.load(DATA)
    dem = city["dem"]
    hillshade = uc.imagery.hillshade(dem)
    slope = uc.imagery.slope(dem)
    figure = hillshade.plot(
        overlay=slope,
        title="Punggol, Singapore — hillshade and slope",
        save=Path(out_dir) / "04_terrain.png",
    )
    del add_basemap
    return {"figure": figure}


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
