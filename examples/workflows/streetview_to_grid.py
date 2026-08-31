"""Street-view color features → point Layer → 250 m grid.

The fixture photo has no verified capture coordinate. The point is placed
at the pocket bbox centre with location_quality='illustrative'.
"""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

DATA = Path(__file__).resolve().parents[1] / "data" / "punggol_pocket"  # licensed photo; location still illustrative
PHOTO_DIR = DATA / "layers"
PHOTO_NAME = "streetview.jpg"


def main(out_dir: str | Path | None = None) -> dict:
    city = uc.load(DATA, layers=["streetview"], lazy=True)
    bbox = city.metadata["bbox"]
    west, south, east, north = bbox
    area = uc.StudyArea.from_bbox(*bbox, place=city.place, city_id="punggol")
    city.study_area = area
    units = uc.units.grid(city, cell_size=250)
    catalog = uc.svi.filename(str(PHOTO_DIR))
    catalog = catalog[catalog["Filename"] == PHOTO_NAME].reset_index(drop=True)
    if catalog.empty:
        raise FileNotFoundError(PHOTO_DIR / PHOTO_NAME)
    features = uc.svi.color(catalog, folder_path=str(PHOTO_DIR))
    features = features.copy()
    features["lon"] = (west + east) / 2.0
    features["lat"] = (south + north) / 2.0
    features["location_quality"] = "illustrative"
    features["source"] = "wikimedia-commons"
    points = uc.svi.as_layer(features, name="streetview_points")
    result = uc.fusion.aggregate(
        points,
        units,
        stat="mean",
        column="Colorfulness",
        indicator="streetview_colorfulness",
    )
    dest = None
    figure = None
    if out_dir is not None:
        dest = Path(out_dir)
        dest.mkdir(parents=True, exist_ok=True)
        figure = result.plot(
            indicator="streetview_colorfulness",
            title="Street-view colorfulness (illustrative location)",
            save=dest / "streetview_colorfulness_grid.png",
        )
        dest = result.save(dest / "streetview_grid")
    return {
        "result": result,
        "layer": points,
        "saved": dest,
        "figure": figure,
        "features": features,
    }


if __name__ == "__main__":
    out = main(Path(__file__).resolve().parents[1] / "output" / "streetview")
    print(out["features"][["Filename", "Colorfulness", "location_quality"]])
    print(out["result"].to_pandas()[["unit_id", "value", "coverage", "quality_flags"]])
