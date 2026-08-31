"""Observed weather + modelled spatial MRT proxy, drawn on city context."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import urbancode as uc
from urbancode.cartography import colorbar
from urbancode.imagery.source import derived_layer, open_raster
from urbancode.plot import plot_indicator_frame

from examples.recipes._common import climate_dir, copy_workflow_static, load_punggol

CAPTION = "Punggol, Singapore — Heat exposure · 2 km × 2 km · 250 m units · EPSG:32648"


# Documented spatial MRT proxy (not a measured campaign).
# Coefficients: +6 °C * clip(NDBI, 0, 1), −4 °C * clip(NDVI, 0, 1).
# Weather is 2024-07-15T14:00 UTC; Sentinel-2 is 2024-07-28 (13-day gap).
MRT_BUILT_COEFF = 6.0
MRT_VEG_COEFF = -4.0
WEATHER_TIME = "2024-07-15T14:00"
IMAGERY_TIME = "2024-07-28T03:15:19Z"


def _mrt_proxy(tair: float, ndvi: np.ndarray, ndbi: np.ndarray) -> np.ndarray:
    veg = np.clip(np.asarray(ndvi, dtype=float), 0.0, 1.0)
    built = np.clip(np.asarray(ndbi, dtype=float), 0.0, 1.0)
    return tair + MRT_BUILT_COEFF * built + MRT_VEG_COEFF * veg


def main(out_dir: str | Path | None = None) -> dict:
    rows = json.loads((climate_dir() / "observations.json").read_text(encoding="utf-8"))
    row = next(item for item in rows if item["city_id"] == "punggol")
    city = load_punggol()
    units = uc.units.grid(city, cell_size=250)
    ndvi_layer = uc.imagery.ndvi(city.layers["sentinel2"])
    ndbi_layer = uc.imagery.ndbi(city.layers["sentinel2"])
    src = open_raster(ndvi_layer)
    tair = float(row["air_temperature_c"])
    mrt_array = _mrt_proxy(tair, src.array_2d, open_raster(ndbi_layer).array_2d)
    air = derived_layer(
        "air_temperature",
        np.full(src.array_2d.shape, tair),
        src,
        processing={"op": "open_meteo_point", "status": "observed"},
        extra={"unit": "degree_celsius"},
    )
    mrt = derived_layer(
        "mean_radiant_temperature",
        mrt_array,
        src,
        processing={
            "op": "ndvi_ndbi_mrt_proxy",
            "status": "modelled",
            "formula": "Tair + 6*clip(NDBI,0,1) - 4*clip(NDVI,0,1)",
        },
        extra={"unit": "degree_celsius"},
    )
    utci = uc.climate.utci(
        air_temperature=air,
        mean_radiant_temperature=mrt,
        wind_speed=float(row["wind_speed_ms"]),
        relative_humidity=float(row["relative_humidity_percent"]),
    )
    utci_u = uc.fusion.aggregate(utci, units, stat="mean", indicator="utci")
    ndvi_u = uc.fusion.aggregate(ndvi_layer, units, stat="mean", indicator="ndvi")
    ndbi_u = uc.fusion.aggregate(ndbi_layer, units, stat="mean", indicator="ndbi")
    buildings = city.layer("buildings").data
    built_layer = city.layer("buildings")
    if buildings is not None and hasattr(buildings, "geom_type"):
        polys = buildings[buildings.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
        built_layer = type(built_layer)(
            name="buildings",
            kind="vector",
            data=polys,
            crs=built_layer.crs,
            source=built_layer.source,
            metadata=built_layer.metadata,
        )
    built_u = uc.fusion.aggregate(built_layer, units, stat="area_fraction", indicator="building_frac")
    # tutorial:start
    combined = uc.fusion.combine(units, utci_u, ndvi_u, ndbi_u, built_u)
    combined.metadata.update(
        {
            "weather_time": row["timestamp"],
            "imagery_time": IMAGERY_TIME,
            "date_gap_days": 13,
            "mrt_proxy": {
                "formula": "Tair + 6*clip(NDBI,0,1) - 4*clip(NDVI,0,1)",
                "built_coeff": MRT_BUILT_COEFF,
                "veg_coeff": MRT_VEG_COEFF,
                "source": "documentation proxy, not a measured campaign",
            },
        }
    )
    for rec in combined.records:
        rec.quality_flags.extend(
            ["modelled_mrt_proxy", "weather_imagery_date_gap"]
        )
    # tutorial:end
    dest = None
    figure = None
    if out_dir is not None:
        dest = Path(out_dir)
        dest.mkdir(parents=True, exist_ok=True)
        fig, axes = plt.subplots(2, 3, figsize=(14.5, 9.0))
        resolved = plot_indicator_frame(
            axes[0, 0],
            combined.to_geopandas(indicator="utci"),
            name="utci",
            unit="degree_celsius",
            context=city,
            alpha=0.7,
            show_scale=False,
        )
        colorbar(fig, axes[0, 0], resolved)
        axes[0, 0].set_title("UTCI on 250 m units (°C)")
        ndvi_layer.plot(ax=axes[0, 1], context=city, title="NDVI (10 m raster)", show_scale=False, locator=False)
        ndbi_layer.plot(ax=axes[0, 2], context=city, title="NDBI (10 m raster)", show_scale=False, locator=False)
        resolved = plot_indicator_frame(
            axes[1, 0],
            combined.to_geopandas(indicator="building_frac"),
            name="building_frac",
            unit="area_fraction",
            context=city,
            alpha=0.55,
            show_scale=False,
        )
        colorbar(fig, axes[1, 0], resolved)
        axes[1, 0].set_title("Building fraction + footprints")
        table = combined.to_pandas().pivot_table(
            index="unit_id", columns="indicator", values="value", aggfunc="first"
        )
        overlap = combined.to_geopandas(indicator="utci").copy()
        joined = overlap.merge(table, left_on="unit_id", right_index=True, how="left")
        hot = joined["utci"] >= joined["utci"].median()
        bare = joined["ndvi"] <= joined["ndvi"].median()
        joined["overlap"] = np.where(hot & bare, 1.0, 0.0)
        plot_indicator_frame(
            axes[1, 1],
            joined,
            column="overlap",
            name="coverage",
            unit="coverage",
            context=city,
            vmin=0,
            vmax=1,
            cmap="OrRd",
            alpha=0.65,
            show_scale=False,
        )
        axes[1, 1].set_title("High UTCI ∩ low NDVI (overlap, not cause)")
        city.plot(
            ax=axes[1, 2],
            layers=["water", "parks", "buildings", "streets"],
            title="Punggol pocket locator",
            show_scale=True,
            locator=True,
        )
        fig.suptitle(
            f"{CAPTION}\nTair {tair:.1f} °C / RH {row['relative_humidity_percent']}% / "
            f"wind {row['wind_speed_ms']} m/s observed · MRT modelled · {row['timestamp']} UTC"
        )
        fig.tight_layout()
        figure = dest / "real_heat_stress.png"
        fig.savefig(figure, dpi=120, bbox_inches="tight")
        plt.close(fig)
        copy_workflow_static(figure, "real_heat_stress.png")
        dest = combined.save(dest / "utci")
    return {
        "result": combined,
        "layer": utci,
        "figure": figure,
        "saved": dest,
        "inputs": {
            "air_temperature": "Observed",
            "relative_humidity": "Observed",
            "wind_speed": "Observed",
            "mean_radiant_temperature": "Modelled NDVI/NDBI proxy",
        },
    }


if __name__ == "__main__":
    out = main(Path(__file__).resolve().parents[1] / "output" / "real_heat")
    print(out["inputs"], out["result"].to_pandas().groupby("indicator")["value"].mean())
