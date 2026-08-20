"""One panel for the main fusion.aggregate stats."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol


def main(out_dir: str | Path) -> dict:
    city = load_punggol(["streets", "sentinel2", "parks", "pois"])
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    units = uc.units.grid(city, cell_size=250)
    ndvi = uc.imagery.ndvi(city.layers["sentinel2"])
    jobs = {
        "raster mean": uc.fusion.aggregate(ndvi, units, stat="mean", indicator="ndvi"),
        "park area_fraction": uc.fusion.aggregate(
            city.layer("parks"), units, stat="area_fraction", indicator="park_frac"
        ),
        "poi count": uc.fusion.aggregate(
            city.layer("pois"), units, stat="count", indicator="poi_count"
        ),
        "node mean": uc.fusion.aggregate(
            uc.network.accessibility(city["streets"], radius=150),
            units,
            stat="mean",
            indicator="reachability",
            part="nodes",
        ),
        "edge length sum": uc.fusion.aggregate(
            city.layer("streets"),
            units,
            stat="sum",
            column="length",
            indicator="street_length_m",
            part="edges",
        ),
        "nearest_distance": uc.fusion.aggregate(
            city.layer("parks"), units, stat="nearest_distance", indicator="park_near_m"
        ),
    }
    paths = []
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    for ax, (title, result) in zip(axes.ravel(), jobs.items()):
        path = dest / f"{result.records[0].indicator}.png"
        result.plot(title=title, save=path)
        ax.imshow(plt.imread(path))
        ax.set_axis_off()
        ax.set_title(title)
        paths.append(path)
    fig.suptitle("fusion.aggregate on the Punggol 250 m grid")
    panel = dest / "aggregate_punggol.png"
    fig.savefig(panel, dpi=120, bbox_inches="tight")
    plt.close(fig)
    static = copy_to_static(panel, "fusion/aggregate_punggol.png")
    return {
        "result": jobs,
        "figures": [panel, static],
        "artifacts": paths,
        "summary": "six aggregate stats",
        "docs_figures": {"aggregate_punggol.png": "recipes/fusion/aggregate_punggol.png"},
    }


if __name__ == "__main__":
    print(main(Path("examples/output/recipes/fusion/aggregate_punggol"))["summary"])
