"""NDVI, park proximity, and network reachability with city context."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import urbancode as uc
from urbancode.cartography import colorbar
from urbancode.plot import plot_indicator_frame

from examples.recipes._common import copy_workflow_static, load_punggol

CAPTION = "Punggol, Singapore — Green accessibility · 2 km × 2 km · 250 m units · EPSG:32648"


def _typology(ndvi_v, park_v, ndvi_cut, park_cut):
    if ndvi_v is None or park_v is None or np.isnan(ndvi_v) or np.isnan(park_v):
        return None
    green = ndvi_v >= ndvi_cut
    near = park_v <= park_cut
    if green and near:
        return "green-accessible"
    if green and not near:
        return "green-isolated"
    if (not green) and near:
        return "grey-accessible"
    return "grey-isolated"


def main(out_dir: str | Path | None = None) -> dict:
    city = load_punggol()
    units = uc.units.grid(city, cell_size=250)
    ndvi = uc.fusion.aggregate(
        uc.imagery.ndvi(city.layers["sentinel2"]), units, stat="mean", indicator="ndvi"
    )
    parks = uc.fusion.aggregate(
        city.layer("parks"), units, stat="nearest_distance", indicator="park_near_m"
    )
    reach = uc.fusion.aggregate(
        uc.network.accessibility(city["streets"], radius=150, metric="reachability"),
        units,
        stat="mean",
        indicator="reachability",
    )
    combined = uc.fusion.combine(units, ndvi, parks, reach)
    dest = None
    figures = {}
    if out_dir is not None:
        dest = Path(out_dir)
        dest.mkdir(parents=True, exist_ok=True)
        ndvi_g = combined.to_geopandas(indicator="ndvi")
        park_g = combined.to_geopandas(indicator="park_near_m")
        reach_g = combined.to_geopandas(indicator="reachability")
        table = combined.to_pandas().pivot_table(
            index="unit_id", columns="indicator", values="value", aggfunc="first"
        )
        ndvi_cut = float(table["ndvi"].median()) if "ndvi" in table else 0.2
        park_cut = float(table["park_near_m"].median()) if "park_near_m" in table else 100.0
        types = [
            _typology(
                table["ndvi"].get(uid) if "ndvi" in table else None,
                table["park_near_m"].get(uid) if "park_near_m" in table else None,
                ndvi_cut,
                park_cut,
            )
            for uid in ndvi_g["unit_id"]
        ]
        ndvi_g = ndvi_g.copy()
        ndvi_g["typology"] = types
        fig, axes = plt.subplots(2, 4, figsize=(16.8, 8.8))
        maps = (
            (axes[0, 0], ndvi_g, "ndvi", "dimensionless", "NDVI (250 m mean)"),
            (axes[0, 1], park_g, "park_near_m", "metre", "Nearest park polygon (m)"),
            (axes[0, 2], reach_g, "reachability", "count", "Reachability (node count)"),
        )
        for ax, frame, name, unit, title in maps:
            resolved = plot_indicator_frame(
                ax, frame, name=name, unit=unit, context=city, alpha=0.65, show_scale=False
            )
            colorbar(fig, ax, resolved)
            ax.set_title(title)
        colors = {
            "green-accessible": "#1a9850",
            "green-isolated": "#91cf60",
            "grey-accessible": "#fdae61",
            "grey-isolated": "#d73027",
        }
        type_g = ndvi_g.copy()
        type_g["color"] = [colors.get(name, "#bbbbbb") for name in type_g["typology"]]
        plot_indicator_frame(
            axes[0, 3],
            type_g.assign(value=1),
            column="value",
            name="coverage",
            context=city,
            show_scale=False,
            alpha=0.01,
        )
        type_g.plot(ax=axes[0, 3], color=type_g["color"], edgecolor="none", alpha=0.7, zorder=5)
        axes[0, 3].set_title("Typology (median splits, not causal)")
        merged = table.dropna(subset=["ndvi", "park_near_m"], how="any")
        axes[1, 0].scatter(merged["ndvi"], merged["park_near_m"], s=18, c="#2c7bb6", alpha=0.8)
        axes[1, 0].set_xlabel("NDVI")
        axes[1, 0].set_ylabel("Nearest park (m)")
        axes[1, 0].set_title("NDVI vs park distance")
        merged_r = table.dropna(subset=["ndvi", "reachability"], how="any")
        axes[1, 1].scatter(merged_r["ndvi"], merged_r["reachability"], s=18, c="#31a354", alpha=0.8)
        axes[1, 1].set_xlabel("NDVI")
        axes[1, 1].set_ylabel("Reachability (node count)")
        axes[1, 1].set_title("NDVI vs reachability")
        cov = ndvi_g.copy()
        cov["coverage"] = cov["coverage"].fillna(0)
        plot_indicator_frame(
            axes[1, 2],
            cov,
            column="coverage",
            name="coverage",
            unit="coverage",
            context=city,
            missing_style="hatch",
            alpha=0.35,
            show_scale=False,
        )
        axes[1, 2].set_title("NDVI coverage (missing = hatch)")
        counts = Counter(types)
        labels = list(colors)
        axes[1, 3].bar(labels, [int(counts.get(name, 0)) for name in labels], color=[colors[n] for n in labels])
        axes[1, 3].tick_params(axis="x", rotation=25)
        axes[1, 3].set_ylabel("cells")
        axes[1, 3].set_title("Typology counts")
        fig.suptitle(CAPTION + " · correlation, not causation")
        fig.tight_layout()
        panel = dest / "green_accessibility.png"
        fig.savefig(panel, dpi=120, bbox_inches="tight")
        plt.close(fig)
        copy_workflow_static(panel, "green_accessibility.png")
        dest = combined.save(dest / "green_access")
        figures["panel"] = panel
    return {"result": combined, "figures": figures, "saved": dest}


if __name__ == "__main__":
    print(main(Path(__file__).resolve().parents[1] / "output" / "green_access")["result"].to_pandas().head())
