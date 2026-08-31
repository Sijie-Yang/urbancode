"""Multi-city API contract with reproducible synthetic pockets.

Punggol is a real extract. Helsinki and NYC are synthetic fixtures.
This script checks the API and unit_id scheme. It is not a real
city-to-city environmental comparison.
"""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

ROOT = Path(__file__).resolve().parents[1] / "data"
POCKETS = {
    "punggol": ROOT / "real" / "punggol",
    "helsinki": ROOT / "contracts" / "helsinki_synthetic",
    "nyc": ROOT / "contracts" / "nyc_synthetic",
}


def main() -> dict:
    combined = []
    for name, path in POCKETS.items():
        city = uc.load(path, layers=["streets", "sentinel2"], lazy=True)
        bbox = city.metadata["bbox"]
        area = uc.StudyArea.from_bbox(*bbox, place=city.place, city_id=name)
        city.study_area = area
        units = uc.units.grid(city, cell_size=250)
        ndvi = uc.imagery.ndvi(city.layers["sentinel2"].path)
        reach = uc.network.accessibility(
            city["streets"], radius=150, metric="reachability"
        )
        merged = uc.fusion.combine(
            units,
            uc.fusion.aggregate(ndvi, units, stat="mean", indicator="ndvi"),
            uc.fusion.aggregate(reach, units, stat="mean", indicator="reachability"),
        )
        combined.extend(merged.records)
    result = uc.indicators.from_records(combined, on_duplicate="raise")
    table = result.to_pandas()
    return {
        "table": table,
        "cities": sorted(table["city_id"].unique()),
        "indicators": sorted(table["indicator"].unique()),
        "n_records": len(result.records),
    }


if __name__ == "__main__":
    out = main()
    print(out["cities"], out["indicators"], out["n_records"])
