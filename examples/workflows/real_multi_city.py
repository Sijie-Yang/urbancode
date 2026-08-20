"""Three real 2 km pockets: context first, then comparable indicators."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

import urbancode as uc
from urbancode.cartography import colorbar
from urbancode.plot import indicator_style, plot_indicator_frame

from examples.recipes._common import REAL, copy_workflow_static, load_pocket

CITIES = (
    ("punggol", "Punggol, Singapore", "EPSG:32648"),
    ("kallio", "Kallio, Helsinki", "EPSG:32635"),
    ("greenwich_village", "Greenwich Village, New York", "EPSG:32618"),
)
INDICATORS = (
    ("ndvi", "dimensionless", "NDVI"),
    ("reachability", "count", "Reachability"),
    ("park_frac", "area_fraction", "Park fraction"),
    ("building_frac", "area_fraction", "Building fraction"),
)


def _polygons(layer):
    frame = layer.data
    polys = frame[frame.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    return type(layer)(
        name=layer.name,
        kind="vector",
        data=polys,
        crs=layer.crs,
        source=layer.source,
        metadata=layer.metadata,
    )


def main(out_dir: str | Path | None = None) -> dict:
    dest = Path(out_dir) if out_dir else None
    rows = []
    frames: dict[str, dict[str, object]] = {}
    cities = {}
    present = []
    for name, label, _crs in CITIES:
        path = REAL / name
        if not (path / "manifest.json").is_file():
            continue
        present.append((name, label))
        city = load_pocket(name)
        cities[name] = city
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
        parks = uc.fusion.aggregate(
            _polygons(city.layer("parks")), units, stat="area_fraction", indicator="park_frac"
        )
        buildings = uc.fusion.aggregate(
            _polygons(city.layer("buildings")), units, stat="area_fraction", indicator="building_frac"
        )
        merged = uc.fusion.combine(units, ndvi, reach, parks, buildings)
        table = merged.to_pandas()
        table["city_id"] = name
        table["place"] = label
        rows.append(table)
        frames[name] = {ind: merged.to_geopandas(indicator=ind) for ind, _unit, _title in INDICATORS}
    if not rows:
        raise FileNotFoundError("no real pockets under examples/data/real/")
    all_rows = pd.concat(rows, ignore_index=True)
    panel = None
    context_panel = None
    if dest is not None and frames:
        dest.mkdir(parents=True, exist_ok=True)
        fig, axes = plt.subplots(1, len(present), figsize=(4.6 * len(present), 4.6))
        if len(present) == 1:
            axes = [axes]
        for col, (city_id, label) in enumerate(present):
            cities[city_id].plot(
                ax=axes[col],
                layers=["water", "parks", "buildings", "streets"],
                title=label,
                show_scale=True,
                locator=True,
            )
        fig.suptitle("Three 2 km pockets — native streets, buildings, parks, water")
        fig.tight_layout()
        context_panel = dest / "multi_city_context.png"
        fig.savefig(context_panel, dpi=120, bbox_inches="tight")
        plt.close(fig)
        copy_workflow_static(context_panel, "multi_city_context.png")

        fig, axes = plt.subplots(len(INDICATORS), len(present), figsize=(4.4 * len(present), 3.8 * len(INDICATORS)))
        if len(present) == 1:
            axes = axes.reshape(len(INDICATORS), 1)
        shared = {}
        for ind, unit, _title in INDICATORS:
            values = all_rows.loc[all_rows["indicator"] == ind, "value"]
            shared[ind] = indicator_style(ind, unit=unit, values=values)
        for col, (city_id, label) in enumerate(present):
            for row, (ind, unit, title) in enumerate(INDICATORS):
                ax = axes[row, col]
                spec = shared[ind]
                plot_indicator_frame(
                    ax,
                    frames[city_id][ind],
                    name=ind,
                    unit=unit,
                    context=cities[city_id],
                    vmin=spec["vmin"],
                    vmax=spec["vmax"],
                    cmap=spec["cmap"],
                    alpha=0.7,
                    show_scale=False,
                    locator=False,
                )
                if col == len(present) - 1:
                    colorbar(fig, ax, spec)
                if row == 0:
                    ax.set_title(label)
                if col == 0:
                    ax.set_ylabel(title)
        fig.suptitle(
            "Same 250 m constructor. Dates differ; do not rank cities. Grid is support, not the city."
        )
        fig.tight_layout()
        panel = dest / "real_multi_city.png"
        fig.savefig(panel, dpi=120, bbox_inches="tight")
        plt.close(fig)
        copy_workflow_static(panel, "real_multi_city.png")
        summary = (
            all_rows.groupby(["place", "indicator"])["value"]
            .agg(["mean", "median", "count"])
            .reset_index()
        )
        summary.to_csv(dest / "city_indicator_summary.csv", index=False)
        coverage = (
            all_rows.groupby(["place", "indicator"])["coverage"].mean().reset_index()
        )
        coverage.to_csv(dest / "coverage_summary.csv", index=False)
    return {
        "table": all_rows,
        "figures": {"context": context_panel, "panel": panel},
        "panel": panel,
        "cities": [name for name, _label in present],
        "note": "Compare methods, not city essence. Seasons are not shared.",
    }


if __name__ == "__main__":
    out = main(Path(__file__).resolve().parents[1] / "output" / "real_multi_city")
    print(out["table"].groupby(["city_id", "indicator"])["value"].mean())
