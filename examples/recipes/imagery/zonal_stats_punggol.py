"""Mean NDVI inside OSM park polygons."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol


def main(out_dir: str | Path) -> dict:
    city = load_punggol(["sentinel2", "parks"])
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    ndvi = uc.imagery.ndvi(city.layers["sentinel2"])
    zones = uc.imagery.zonal_stats(ndvi, city["parks"], metrics=("mean",))
    parks = dest / "parks.png"
    raster = dest / "ndvi.png"
    choropleth = dest / "park_mean.png"
    city.plot(layers=["parks"], title="OSM parks", save=parks)
    ndvi.plot(title="NDVI", save=raster)
    if hasattr(zones, "plot"):
        zones.plot(title="Park mean NDVI", save=choropleth, column="mean")
    else:
        import geopandas as gpd

        frame = zones if hasattr(zones, "geometry") else zones
        gpd.GeoDataFrame(frame).plot(column="mean")
        plt.title("Park mean NDVI")
        plt.savefig(choropleth, dpi=120, bbox_inches="tight")
        plt.close()
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, path, title in (
        (axes[0], parks, "Parks"),
        (axes[1], raster, "NDVI"),
        (axes[2], choropleth, "Park mean NDVI"),
    ):
        ax.imshow(plt.imread(path))
        ax.set_axis_off()
        ax.set_title(title)
    panel = dest / "zonal_stats_punggol.png"
    fig.savefig(panel, dpi=120, bbox_inches="tight")
    plt.close(fig)
    static = copy_to_static(panel, "imagery/zonal_stats_punggol.png")
    table = dest / "zonal_stats.csv"
    frame = zones.data if hasattr(zones, "data") else zones
    if hasattr(frame, "to_csv"):
        frame.drop(columns="geometry", errors="ignore").to_csv(table, index=False)
    return {
        "result": zones,
        "figures": [panel, static],
        "artifacts": [table, parks, raster, choropleth],
        "summary": "park mean NDVI",
        "docs_figures": {"zonal_stats_punggol.png": "recipes/imagery/zonal_stats_punggol.png"},
    }


if __name__ == "__main__":
    print(main(Path("examples/output/recipes/imagery/zonal_stats_punggol"))["summary"])
