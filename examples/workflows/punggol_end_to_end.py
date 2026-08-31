"""Docs figure builder for the Punggol profile. Not a tutorial.

Copy the snippet on docs/getting_started/quickstart instead of
importing this file.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

import urbancode as uc
from urbancode.cartography import colorbar
from urbancode.plot import plot_indicator_frame

from examples.recipes._common import copy_workflow_static, load_punggol

DATA = Path(__file__).resolve().parents[1] / "data" / "real" / "punggol"
CAPTION = "Punggol, Singapore — 2 km × 2 km pocket · 250 m units · EPSG:32648"


def main(out_dir: str | Path | None = None) -> dict:
    city = load_punggol()
    units = uc.units.grid(city, cell_size=250)
    ndvi = uc.imagery.ndvi(city.layers["sentinel2"].path)
    ndbi = uc.imagery.ndbi(city.layers["sentinel2"].path)
    slope = uc.imagery.slope(city.layers["dem"].path)
    reach = uc.network.accessibility(city["streets"], radius=150, metric="reachability")
    ndvi_result = uc.fusion.aggregate(ndvi, units, stat="mean", indicator="ndvi")
    ndbi_result = uc.fusion.aggregate(ndbi, units, stat="mean", indicator="ndbi")
    slope_result = uc.fusion.aggregate(slope, units, stat="mean", indicator="slope")
    reach_result = uc.fusion.aggregate(reach, units, stat="mean", indicator="reachability")
    combined = uc.fusion.combine(units, ndvi_result, ndbi_result, slope_result, reach_result)
    table = combined.to_pandas()
    dest = None
    figures: dict[str, Path] = {}
    if out_dir is not None:
        dest = Path(out_dir)
        dest.mkdir(parents=True, exist_ok=True)
        fig, axes = plt.subplots(2, 3, figsize=(14.5, 9.2))
        city.plot(
            ax=axes[0, 0],
            layers=["water", "parks", "buildings", "streets"],
            title="Context",
            show_scale=True,
            show_north=True,
            locator=True,
        )
        resolved = plot_indicator_frame(
            axes[0, 1],
            combined.to_geopandas(indicator="reachability"),
            name="reachability",
            unit="count",
            context=city,
            show_scale=False,
            alpha=0.7,
        )
        colorbar(fig, axes[0, 1], resolved)
        axes[0, 1].set_title("Network reachability (grid + streets)")
        ndvi.plot(ax=axes[0, 2], context=city, title="NDVI (10 m raster)", alpha=0.85, show_scale=False, locator=False)
        ndbi.plot(ax=axes[1, 0], context=city, title="NDBI (10 m raster)", alpha=0.85, show_scale=False, locator=False)
        slope.plot(ax=axes[1, 1], context=city, title="Slope (DEM raster)", alpha=0.85, show_scale=False, locator=False)
        axes[1, 2].axis("off")
        means = table.groupby("indicator")["value"].mean()
        axes[1, 2].text(
            0.0,
            0.55,
            f"{CAPTION}\nSentinel-2 2024-07-28 · OSM ODbL · Copernicus DEM\n\n"
            "Core profile means (250 m units)\n"
            + "\n".join(f"{k}: {v:.3f}" for k, v in means.items())
            + "\n\nSpatial support: streets/buildings native; "
            "NDVI/NDBI/slope native raster; reachability fused to grid.\n"
            "Climate and street-view stay in their own workflows.",
            va="center",
            fontsize=8,
        )
        fig.suptitle(CAPTION + " · core urban profile")
        fig.tight_layout()
        panel = dest / "punggol_urban_profile.png"
        fig.savefig(panel, dpi=120, bbox_inches="tight")
        plt.close(fig)
        copy_workflow_static(panel, "punggol_urban_profile.png")
        figures["panel"] = panel
        saved = combined.save(dest / "punggol_indicators")
        dest = saved
    return {
        "units": units,
        "result": combined,
        "table": table,
        "saved": dest,
        "figures": figures,
        "coverage": [r.coverage for r in ndvi_result.records],
        "receipts": list(combined.metadata.get("provenance") or []),
    }


if __name__ == "__main__":
    out = main(Path(__file__).resolve().parents[1] / "output" / "punggol")
    print(out["table"].groupby("indicator")["value"].mean())
