"""Shared grid / hexgrid / from_layer panel."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol


def run_units(out_dir: str | Path) -> dict:
    city = load_punggol(["parks"])
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    squares = uc.units.grid(city, cell_size=250)
    hexes = uc.units.hexgrid(city, cell_size=250)
    parks = uc.units.from_layer(
        city.layer("parks"),
        city_id="punggol",
        study_area=city.study_area,
    )
    paths = {
        "250 m grid": dest / "grid.png",
        "hexgrid": dest / "hex.png",
        "from_layer parks": dest / "parks.png",
    }
    _plot_units(squares, paths["250 m grid"], "250 m grid")
    _plot_units(hexes, paths["hexgrid"], "hexgrid")
    _plot_units(parks, paths["from_layer parks"], "from_layer parks")
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, (title, path) in zip(axes, paths.items()):
        ax.imshow(plt.imread(path))
        ax.set_axis_off()
        ax.set_title(title)
    fig.suptitle("Punggol analysis units")
    panel = dest / "units_punggol.png"
    fig.savefig(panel, dpi=120, bbox_inches="tight")
    plt.close(fig)
    static = copy_to_static(panel, "units/units_punggol.png")
    sample = dest / "unit_ids.txt"
    sample.write_text(
        "grid: " + ", ".join(squares.unit_ids[:3]) + "\n"
        "hex: " + ", ".join(hexes.unit_ids[:3]) + "\n"
        "parks: " + ", ".join(parks.unit_ids[:3]) + "\n",
        encoding="utf-8",
    )
    return {
        "result": {"grid": squares, "hexgrid": hexes, "from_layer": parks},
        "figures": [panel, static],
        "artifacts": [sample],
        "summary": (
            f"grid={len(squares.unit_ids)} hex={len(hexes.unit_ids)} "
            f"parks={len(parks.unit_ids)}"
        ),
        "docs_figures": {"units_punggol.png": "recipes/units/units_punggol.png"},
    }


def _plot_units(units, path: Path, title: str) -> None:
    layer = uc.Layer(
        name="units",
        kind="vector",
        data=units.frame,
        crs=units.crs or units.metric_crs,
        source="urbancode.units",
    )
    layer.plot(title=title, save=path)
