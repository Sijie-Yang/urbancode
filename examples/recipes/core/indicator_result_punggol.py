"""IndicatorResult to_pandas / to_geopandas / plot / save / load."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol


def main(out_dir: str | Path) -> dict:
    city = load_punggol(["sentinel2"])
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    units = uc.units.grid(city, cell_size=250)
    result = uc.fusion.aggregate(
        uc.imagery.ndvi(city.layers["sentinel2"]), units, stat="mean", indicator="ndvi"
    )
    table = result.to_pandas()
    gdf = result.to_geopandas(indicator="ndvi")
    figure = result.plot(indicator="ndvi", title="IndicatorResult.plot", save=dest / "indicator_result_punggol.png")
    static = copy_to_static(figure, "core/indicator_result_punggol.png")
    saved = result.save(dest / "ndvi_result")
    loaded = uc.IndicatorResult.load(saved)
    table.to_csv(dest / "ndvi.csv", index=False)
    return {
        "result": loaded,
        "figures": [figure, static],
        "artifacts": [saved, dest / "ndvi.csv"],
        "summary": f"rows={len(table)} geoms={len(gdf)} reloaded={len(loaded.records)}",
        "docs_figures": {
            "indicator_result_punggol.png": "recipes/core/indicator_result_punggol.png"
        },
    }
