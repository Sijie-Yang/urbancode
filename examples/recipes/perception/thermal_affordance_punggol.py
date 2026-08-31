"""TCIS thermal affordance on licensed Punggol photos."""

from __future__ import annotations

from pathlib import Path

from examples.recipes._common import copy_to_static, load_punggol
from examples.research_cases.thermal_comfort_in_sight import (
    figure_vata,
    image_layer,
    predict_or_load,
)


def main(out_dir: str | Path) -> dict:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    city = load_punggol()
    units = __import__("urbancode", fromlist=["units"]).units.grid(city, cell_size=250)
    images = image_layer()
    predictions = predict_or_load(images, mode="case")
    figure = figure_vata(city, predictions, units, dest)
    static = copy_to_static(figure, "perception/thermal_affordance_punggol.png")
    return {
        "result": predictions,
        "figures": [figure, static],
        "artifacts": [],
        "summary": f"n={len(predictions.data)} thermal_affordance Layer",
        "docs_figures": {
            "tcis_thermal_affordance.png": "recipes/perception/thermal_affordance_punggol.png"
        },
    }


if __name__ == "__main__":
    print(main(Path("examples/output/recipes/perception/thermal_affordance_punggol"))["summary"])
