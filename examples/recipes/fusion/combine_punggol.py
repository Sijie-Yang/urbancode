"""Combine NDVI and reachability onto one IndicatorResult."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol


def main(out_dir: str | Path) -> dict:
    city = load_punggol(["streets", "sentinel2"])
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    units = uc.units.grid(city, cell_size=250)
    ndvi = uc.fusion.aggregate(
        uc.imagery.ndvi(city.layers["sentinel2"]), units, stat="mean", indicator="ndvi"
    )
    reach = uc.fusion.aggregate(
        uc.network.accessibility(city["streets"], radius=150),
        units,
        stat="mean",
        indicator="reachability",
    )
    combined = uc.fusion.combine(units, ndvi, reach)
    figure = combined.plot(
        indicator="ndvi",
        title="Combined result — NDVI (reachability is the sibling indicator)",
        save=dest / "combine_punggol.png",
    )
    static = copy_to_static(figure, "fusion/combine_punggol.png")
    table = dest / "combined.csv"
    combined.to_pandas().to_csv(table, index=False)
    return {
        "result": combined,
        "figures": [figure, static],
        "artifacts": [table],
        "summary": f"indicators={sorted(set(combined.to_pandas()['indicator']))}",
        "docs_figures": {"combine_punggol.png": "recipes/fusion/combine_punggol.png"},
    }


if __name__ == "__main__":
    print(main(Path("examples/output/recipes/fusion/combine_punggol"))["summary"])
