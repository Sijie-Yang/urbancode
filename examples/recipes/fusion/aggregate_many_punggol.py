"""Batch-aggregate TCIS columns onto Punggol 250 m units."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol
from examples.research_cases.thermal_comfort_in_sight import image_layer, predict_or_load


def main(out_dir: str | Path) -> dict:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    city = load_punggol()
    units = uc.units.grid(city, cell_size=250)
    predictions = predict_or_load(image_layer(), mode="case")
    result = uc.fusion.aggregate_many(
        predictions,
        units,
        columns={
            "thermal_affordance": {"indicator": "thermal_affordance", "unit": "score_0_5"},
            "shading_area": {"indicator": "perceived_shading", "unit": "score_0_5"},
            "greenery_rate": {"indicator": "perceived_greenery", "unit": "score_0_5"},
        },
        stat="mean",
    )
    figure = result.plot(
        indicator="thermal_affordance",
        title="aggregate_many — mean VATA (unobserved units empty)",
        save=dest / "aggregate_many_punggol.png",
        context=city,
        missing_style="hatch",
    )
    static = copy_to_static(figure, "fusion/aggregate_many_punggol.png")
    return {
        "result": result,
        "figures": [figure, static],
        "artifacts": [],
        "summary": f"indicators={sorted({r.indicator for r in result.records})}",
        "docs_figures": {
            "aggregate_many_punggol.png": "recipes/fusion/aggregate_many_punggol.png"
        },
    }


if __name__ == "__main__":
    print(main(Path("examples/output/recipes/fusion/aggregate_many_punggol"))["summary"])
