"""Synthetic meteorological inputs → UTCI → grid. Not Punggol weather."""

from __future__ import annotations

from pathlib import Path

import numpy as np

import urbancode as uc
from urbancode.imagery.source import derived_layer, open_raster

DATA = Path(__file__).resolve().parents[1] / "data" / "real" / "punggol"


def main(out_dir: str | Path | None = None) -> dict:
    city = uc.load(DATA, layers=["dem"], lazy=True)
    bbox = city.metadata["bbox"]
    area = uc.StudyArea.from_bbox(*bbox, place=city.place, city_id="punggol")
    city.study_area = area
    units = uc.units.grid(city, cell_size=250)
    src = open_raster(city.layers["dem"].path)
    air = derived_layer(
        "air_temperature",
        np.full(src.array_2d.shape, 31.0),
        src,
        processing={"op": "synthetic_meteorology"},
        extra={"unit": "degree_celsius"},
    )
    utci = uc.climate.utci(
        air_temperature=air,
        mean_radiant_temperature=air,
        wind_speed=0.8,
        relative_humidity=70,
    )
    result = uc.fusion.aggregate(utci, units, stat="mean", indicator="utci")
    dest = None
    figure = None
    if out_dir is not None:
        dest = Path(out_dir)
        dest.mkdir(parents=True, exist_ok=True)
        figure = utci.plot(
            title="Synthetic UTCI (not Punggol weather)",
            save=dest / "utci_synthetic.png",
        )
        dest = result.save(dest / "utci")
    return {"result": result, "saved": dest, "layer": utci, "figure": figure}


if __name__ == "__main__":
    out = main(Path(__file__).resolve().parents[1] / "output" / "climate")
    print(out["result"].to_pandas()["value"].describe())
