"""Zonal mean NDVI for park polygons."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

DATA = Path(__file__).resolve().parents[1] / "data" / "punggol_pocket"


def main(out_dir: str | Path, *, add_basemap: bool = False) -> dict[str, Path]:
    city = uc.load(DATA)
    ndvi = uc.imagery.ndvi(city["sentinel2"])
    stats = uc.imagery.zonal_stats(ndvi, city["parks"], metrics=["mean"])
    out = Path(out_dir)
    figure = stats.plot(
        column="mean",
        title="Punggol, Singapore — zonal NDVI in parks",
        save=out / "05_zonal_ndvi.png",
    )
    table = stats.save(out / "05_zonal_ndvi.csv")
    del add_basemap
    return {"figure": figure, "table": table}


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
