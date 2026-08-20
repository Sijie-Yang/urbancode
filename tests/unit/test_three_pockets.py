from __future__ import annotations

from pathlib import Path

import pytest

import urbancode as uc
from urbancode.area import StudyArea

ROOT = Path(__file__).resolve().parents[2] / "examples" / "data"
POCKETS = {
    "punggol": ROOT / "real" / "punggol" if (ROOT / "real" / "punggol" / "manifest.json").exists() else ROOT / "punggol_pocket",
    "helsinki": ROOT / "contracts" / "helsinki_synthetic",
    "nyc": ROOT / "contracts" / "nyc_synthetic",
}


@pytest.mark.parametrize("name", list(POCKETS))
def test_pocket_exists(name: str) -> None:
    path = POCKETS[name]
    assert (path / "manifest.json").exists()
    assert (path / "layers" / "streets.graphml").exists()
    assert (path / "layers" / "sentinel2.tif").exists()


def test_three_pockets_same_grid_scheme() -> None:
    pytest.importorskip("geopandas")
    pytest.importorskip("rasterio")
    pytest.importorskip("networkx")
    for path in POCKETS.values():
        if not path.is_dir():
            pytest.skip(f"missing pocket {path}")

    combined_records = []
    id_prefixes = set()
    for name, path in POCKETS.items():
        city = uc.load(path, layers=["streets", "sentinel2"], lazy=True)
        bbox = city.metadata["bbox"]
        area = StudyArea.from_bbox(*bbox, place=city.place, city_id=name)
        city.study_area = area
        units = uc.units.grid(city, cell_size=250)
        assert units.unit_ids
        assert all(uid.startswith("grid:") and ":250:" in uid for uid in units.unit_ids)
        id_prefixes.add(units.unit_ids[0].rsplit(":", 2)[0])
        ndvi = uc.imagery.ndvi(city.layers["sentinel2"].path)
        reach = uc.network.accessibility(city["streets"], radius=150, metric="reachability")
        ndvi_result = uc.fusion.aggregate(ndvi, units, stat="mean", indicator="ndvi")
        reach_result = uc.fusion.aggregate(reach, units, stat="mean", indicator="reachability")
        merged = uc.fusion.combine(units, ndvi_result, reach_result)
        assert {r.city_id for r in merged.records} == {name}
        combined_records.extend(merged.records)

    cities = {r.city_id for r in combined_records}
    assert cities == {"punggol", "helsinki", "nyc"}
    indicators = {r.indicator for r in combined_records}
    assert "ndvi" in indicators and "reachability" in indicators
    assert len(id_prefixes) == 3
