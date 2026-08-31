"""Street photos → points → grid, with streets and buildings as context."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

import urbancode as uc
from urbancode.cartography import colorbar, to_crs
from urbancode.plot import plot_indicator_frame

from examples.recipes._common import REAL, copy_workflow_static, load_punggol, streetview_dir

CAPTION = "Punggol, Singapore — Street experience · 2 km × 2 km · n photos · EPSG:32648"


def main(out_dir: str | Path | None = None) -> dict:
    catalog_path = REAL / "streetview" / "catalog.json"
    if not catalog_path.is_file():
        raise FileNotFoundError(
            "examples/data/real/streetview/catalog.json missing; "
            "run scripts/data/build_streetview_cases.py"
        )
    rows = [row for row in json.loads(catalog_path.read_text(encoding="utf-8")) if row.get("city_id") == "punggol"]
    if len(rows) < 1:
        raise RuntimeError("no geotagged Punggol photos; spatial street-experience stays blocked")
    # tutorial:start
    frame = pd.DataFrame(rows)
    folder = REAL / "streetview" / "punggol"
    if not folder.is_dir():
        folder = streetview_dir()
    catalog = uc.svi.filename(str(folder))
    features = uc.svi.color(catalog, folder_path=str(folder))
    features["stem"] = features["Filename"].map(lambda name: Path(name).stem)
    frame = frame.copy()
    frame["stem"] = frame["path"].map(lambda name: Path(name).stem.replace(".jpg", ""))
    merged = features.merge(frame, on="stem", how="inner")
    if merged.empty:
        merged = frame.copy()
        merged["Colorfulness"] = float("nan")
    points = uc.svi.as_layer(merged, name="streetview_points")
    city = load_punggol()
    units = uc.units.grid(city, cell_size=250)
    color = uc.fusion.aggregate(
        points, units, stat="mean", column="Colorfulness", indicator="colorfulness"
    )
    count = uc.fusion.aggregate(points, units, stat="count", indicator="photo_count")
    ndvi_layer = uc.imagery.ndvi(city.layers["sentinel2"])
    ndvi = uc.fusion.aggregate(ndvi_layer, units, stat="mean", indicator="ndvi")
    reach = uc.fusion.aggregate(
        uc.network.accessibility(city["streets"], radius=150, metric="reachability"),
        units,
        stat="mean",
        indicator="reachability",
    )
    combined = uc.fusion.combine(units, color, count, ndvi, reach)
    # tutorial:end
    dest = None
    figure = None
    if out_dir is not None:
        dest = Path(out_dir)
        dest.mkdir(parents=True, exist_ok=True)
        fig, axes = plt.subplots(2, 3, figsize=(14.5, 9.0))
        photo = next(folder.glob("*.jpg"), None)
        if photo is not None:
            axes[0, 0].imshow(plt.imread(photo))
            axes[0, 0].set_title(f"Sample photo ({photo.name})")
        axes[0, 0].set_axis_off()
        city.plot(
            ax=axes[0, 1],
            layers=["water", "parks", "buildings", "streets"],
            title=f"Photo locations (n={len(rows)})",
            show_scale=True,
            locator=False,
        )
        pts = to_crs(points.data, city.study_area.metric_crs)
        if pts is not None and hasattr(pts, "plot"):
            pts.plot(ax=axes[0, 1], color="#c0392b", markersize=36, zorder=9)
        resolved = plot_indicator_frame(
            axes[0, 2],
            combined.to_geopandas(indicator="photo_count"),
            name="photo_count",
            unit="count",
            context=city,
            alpha=0.7,
            show_scale=False,
        )
        colorbar(fig, axes[0, 2], resolved)
        axes[0, 2].set_title("Grid observation count")
        resolved = plot_indicator_frame(
            axes[1, 0],
            combined.to_geopandas(indicator="colorfulness"),
            name="colorfulness",
            unit="colorfulness",
            context=city,
            alpha=0.85,
            missing_style="transparent",
            show_scale=False,
        )
        colorbar(fig, axes[1, 0], resolved)
        axes[1, 0].set_title(f"Colorfulness (observed cells only, n={len(rows)})")
        ndvi_layer.plot(ax=axes[1, 1], context=city, title="NDVI context (10 m)", show_scale=False, locator=False)
        resolved = plot_indicator_frame(
            axes[1, 2],
            combined.to_geopandas(indicator="reachability"),
            name="reachability",
            unit="count",
            context=city,
            alpha=0.65,
            show_scale=False,
        )
        colorbar(fig, axes[1, 2], resolved)
        axes[1, 2].set_title("Network reachability + streets")
        fig.suptitle(CAPTION.replace("n photos", f"n={len(rows)} photos") + " · sampling first, then features")
        fig.tight_layout()
        figure = dest / "street_experience.png"
        fig.savefig(figure, dpi=120, bbox_inches="tight")
        plt.close(fig)
        copy_workflow_static(figure, "street_experience.png")
        dest = combined.save(dest / "street_experience")
    return {"result": combined, "layer": points, "figure": figure, "saved": dest, "n": len(rows)}


if __name__ == "__main__":
    print(main(Path(__file__).resolve().parents[1] / "output" / "street_experience")["n"])
