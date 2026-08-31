"""Shared DEM / slope / aspect / hillshade panel."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol


def run_terrain(out_dir: str | Path) -> dict:
    city = load_punggol(["dem"])
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    dem = city.layer("dem")
    slope = uc.imagery.slope(dem)
    aspect = uc.imagery.aspect(dem)
    shade = uc.imagery.hillshade(dem)
    paths = {
        "DEM": dest / "dem.png",
        "Slope": dest / "slope.png",
        "Aspect": dest / "aspect.png",
        "Hillshade": dest / "hillshade.png",
    }
    dem.plot(title="DEM (m)", save=paths["DEM"])
    slope.plot(title="Slope (degree)", save=paths["Slope"])
    aspect.plot(title="Aspect (degree from north)", save=paths["Aspect"])
    shade.plot(title="Hillshade", save=paths["Hillshade"])
    fig, axes = plt.subplots(2, 2, figsize=(9, 8))
    for ax, (title, path) in zip(axes.ravel(), paths.items()):
        ax.imshow(plt.imread(path))
        ax.set_axis_off()
        ax.set_title(title)
    fig.suptitle("Punggol Copernicus DEM terrain")
    panel = dest / "terrain_punggol.png"
    fig.savefig(panel, dpi=120, bbox_inches="tight")
    plt.close(fig)
    static = copy_to_static(panel, "imagery/terrain_punggol.png")
    return {
        "result": {"dem": dem, "slope": slope, "aspect": aspect, "hillshade": shade},
        "figures": [panel, static],
        "artifacts": list(paths.values()),
        "summary": "DEM slope aspect hillshade",
        "docs_figures": {"terrain_punggol.png": "recipes/imagery/terrain_punggol.png"},
    }
