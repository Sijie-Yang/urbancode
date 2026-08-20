"""Build a geolocated image Layer from the licensed Punggol catalog."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol
from examples.research_cases._tcis_data import punggol_catalog


def main(out_dir: str | Path) -> dict:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    city = load_punggol(["streets", "buildings", "water"])
    frame = punggol_catalog()
    images = uc.images.from_table(
        frame,
        id_column="image_id",
        path_column="image_path",
        lon="longitude",
        lat="latitude",
        view_type="streetview",
        source="wikimedia-commons",
        license="CC BY-SA 4.0",
        city_id="punggol",
        name="punggol_photos",
    )
    figure = images.plot(
        title="Punggol licensed street photos (n=8, not a census)",
        save=dest / "from_table_punggol.png",
        context=city,
        column=None,
    )
    static = copy_to_static(figure, "images/from_table_punggol.png")
    return {
        "result": images,
        "figures": [figure, static],
        "artifacts": [],
        "summary": f"n={len(frame)} view_type=streetview",
        "docs_figures": {"from_table_punggol.png": "recipes/images/from_table_punggol.png"},
    }


if __name__ == "__main__":
    print(main(Path("examples/output/recipes/images/from_table_punggol"))["summary"])
