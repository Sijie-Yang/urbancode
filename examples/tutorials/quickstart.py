"""Canonical 15-minute quickstart. Docs and tests share this script.

Run from the repository root after ``pip install "urbancode[standard]"``.
The pocket ``examples/data/real/punggol`` is a committed docs fixture;
it is not inside the PyPI wheel.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import urbancode as uc

ROOT = Path(__file__).resolve().parents[2]
PUNGGOL = ROOT / "examples" / "data" / "real" / "punggol"

EXPECTED = {
    "n_cells": 81,
    "ndvi_mean": 0.208,
    "reach_nulls": 32,
    "n_nodes": 1425,
}


def run(data: str | Path | None = None) -> dict[str, Any]:
    city = uc.load(data or PUNGGOL, lazy=True)
    units = uc.units.grid(city, cell_size=250)
    ndvi = uc.imagery.ndvi(city.layers["sentinel2"])
    reach = uc.network.accessibility(
        city["streets"], radius=150, metric="reachability"
    )
    ndvi_grid = uc.fusion.aggregate(ndvi, units, stat="mean", indicator="ndvi")
    reach_grid = uc.fusion.aggregate(
        reach, units, stat="mean", indicator="reachability"
    )
    result = uc.fusion.combine(units, ndvi_grid, reach_grid)
    return {
        "city": city,
        "units": units,
        "ndvi": ndvi,
        "reach": reach,
        "ndvi_grid": ndvi_grid,
        "reach_grid": reach_grid,
        "result": result,
        "n_cells": len(units.frame),
        "ndvi_mean": round(float(ndvi_grid.to_pandas()["value"].mean()), 3),
        "reach_nulls": int(reach_grid.to_pandas()["value"].isna().sum()),
        "n_nodes": reach.data.number_of_nodes(),
    }


if __name__ == "__main__":
    out = run()
    print(out["city"].place)
    print(out["n_cells"], out["units"].kind, out["units"].metric_crs)
    print(out["ndvi"].kind, out["ndvi"].data.shape)
    print(out["reach"].kind, out["n_nodes"])
    print(out["ndvi_mean"], out["reach_nulls"])
    print(out["result"].to_pandas().groupby("indicator")["value"].mean())
