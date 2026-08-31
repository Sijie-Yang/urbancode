"""Point Layer from geotagged photos, or an explicitly illustrative fallback."""

from __future__ import annotations

import json
from pathlib import Path

import urbancode as uc

from examples.recipes._common import REAL, copy_to_static, load_punggol, streetview_dir


def main(out_dir: str | Path) -> dict:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    city = load_punggol(["streets"])
    catalog_path = REAL / "streetview" / "catalog.json"
    if catalog_path.is_file():
        rows = json.loads(catalog_path.read_text(encoding="utf-8"))
        punggol = [row for row in rows if row.get("city_id") == "punggol"]
    else:
        punggol = []
    if punggol:
        import pandas as pd

        frame = pd.DataFrame(punggol)
        quality = "commons-geosearch"
    else:
        import pandas as pd

        folder = streetview_dir()
        frame = uc.svi.filename(str(folder))
        west, south, east, north = city.metadata["bbox"]
        frame = frame.copy()
        frame["longitude"] = (west + east) / 2.0
        frame["latitude"] = (south + north) / 2.0
        frame["location_quality"] = "illustrative"
        quality = "illustrative"
    points = uc.svi.as_layer(frame, name="streetview_points")
    title = (
        "Geotagged Commons photos"
        if quality != "illustrative"
        else "Illustrative location (not a real observation)"
    )
    figure = points.plot(title=title, save=dest / "as_layer_punggol.png")
    static = copy_to_static(figure, "streetview/as_layer_punggol.png")
    return {
        "result": points,
        "figures": [figure, static],
        "artifacts": [],
        "summary": f"n={len(frame)} location_quality={quality}",
        "docs_figures": {"as_layer_punggol.png": "recipes/streetview/as_layer_punggol.png"},
    }
