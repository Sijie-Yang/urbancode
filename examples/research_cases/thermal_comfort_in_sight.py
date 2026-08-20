"""Thermal Comfort in Sight research case, rewritten on UrbanCode objects.

VATA (thermal_affordance) is visual thermal affordance. UTCI is a
physical heat-stress index. They can be compared; they are not substitutes.
Eight licensed Commons photos are a sample, not a Punggol census.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import urbancode as uc
from urbancode.cartography import colorbar
from urbancode.city import Layer
from urbancode.imagery.source import derived_layer, open_raster
from urbancode.plot import plot_indicator_frame
from urbancode.provenance import stamp_layer

from examples.recipes._common import (
    STATIC_WORKFLOWS,
    climate_dir,
    copy_to_static,
    copy_workflow_static,
    load_punggol,
)
from examples.research_cases._tcis_data import (
    CASE,
    CITATION,
    load_predictions,
    punggol_catalog,
    sha256,
)

CAPTION = (
    "Punggol, Singapore — Thermal Comfort in Sight · 8 licensed photos · "
    "not a neighbourhood census · EPSG:32648"
)
VPI_COLUMNS = (
    "visual_comfort",
    "temp_intensity",
    "sun_intensity",
    "humidity_inference",
    "wind_inference",
    "shading_area",
    "greenery_rate",
)
IF_COLUMNS = (
    "seg_vegetation",
    "seg_sky",
    "seg_building",
    "Colorfulness",
    "shading_area",
)


def _mrt_proxy(tair: float, ndvi: np.ndarray, ndbi: np.ndarray) -> np.ndarray:
    veg = np.clip(np.asarray(ndvi, dtype=float), 0.0, 1.0)
    built = np.clip(np.asarray(ndbi, dtype=float), 0.0, 1.0)
    return tair + 6.0 * built - 4.0 * veg


def image_layer() -> Layer:
    frame = punggol_catalog()
    return uc.images.from_table(
        frame,
        id_column="image_id",
        path_column="image_path",
        lon="longitude",
        lat="latitude",
        view_type="streetview",
        source="wikimedia-commons",
        license="CC BY-SA 4.0",
        city_id="punggol",
        name="tcis_photos",
    )


def predict_or_load(images: Layer, *, mode: str = "case") -> Layer:
    if mode == "full":
        return uc.perception.thermal_affordance(images, device="cpu", include_features=True)
    precomputed = load_predictions()
    if precomputed is not None:
        return _layer_from_predictions(images, precomputed)
    try:
        return uc.perception.thermal_affordance(images, device="cpu", include_features=True)
    except Exception:
        if mode == "tiny":
            raise
        raise RuntimeError(
            "TCIS predictions are missing. Run with mode='full' after "
            "installing urbancode[perception], or commit predictions.csv "
            "from a real TCIS run. Do not invent a city-scale map."
        )


def _layer_from_predictions(images: Layer, predicted: pd.DataFrame) -> Layer:
    frame = images.data.merge(predicted, on="image_id", how="left", suffixes=("", "_pred"))
    layer = Layer(
        name="thermal_affordance",
        kind="vector",
        data=frame,
        crs=images.crs,
        source="urbancode.perception.thermal_affordance",
        metadata={
            "processing": {
                "op": "thermal_affordance",
                "backend": "tcis",
                "mode": "precomputed",
            },
            "column": "thermal_affordance",
            "unit": "score_0_5",
            "model": {
                "model_id": "tcis-twostage-resnet50",
                "model_version": "tcis-code4",
                "source": "committed TCIS outputs on licensed Commons photos",
                "citation": CITATION,
            },
            "parent_layer_ids": [(images.metadata or {}).get("provenance_id")],
            "n_images": int(len(frame)),
            "sample_warning": "n=8 licensed photos; not a Punggol census",
        },
    )
    stamp_layer(
        layer,
        method="thermal_affordance",
        assumptions=[
            "VATA is visual thermal affordance, not measured comfort and not UTCI",
            "scores are committed outputs of the TCIS model on these photos",
        ],
    )
    return layer


def heat_layers(city):
    rows = json.loads((climate_dir() / "observations.json").read_text(encoding="utf-8"))
    row = next(item for item in rows if item["city_id"] == "punggol")
    ndvi_layer = uc.imagery.ndvi(city.layers["sentinel2"])
    ndbi_layer = uc.imagery.ndbi(city.layers["sentinel2"])
    src = open_raster(ndvi_layer)
    tair = float(row["air_temperature_c"])
    mrt = derived_layer(
        "mean_radiant_temperature",
        _mrt_proxy(tair, src.array_2d, open_raster(ndbi_layer).array_2d),
        src,
        processing={
            "op": "ndvi_ndbi_mrt_proxy",
            "status": "modelled",
            "formula": "Tair + 6*clip(NDBI,0,1) - 4*clip(NDVI,0,1)",
        },
        extra={"unit": "degree_celsius"},
    )
    air = derived_layer(
        "air_temperature",
        np.full(src.array_2d.shape, tair),
        src,
        processing={"op": "open_meteo_point", "status": "observed"},
        extra={"unit": "degree_celsius"},
    )
    utci = uc.climate.utci(
        air_temperature=air,
        mean_radiant_temperature=mrt,
        wind_speed=float(row["wind_speed_ms"]),
        relative_humidity=float(row["relative_humidity_percent"]),
    )
    return ndvi_layer, ndbi_layer, utci


def _save(fig, dest: Path, name: str, workflow: bool = True) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / name
    fig.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    if workflow:
        copy_workflow_static(path, name)
        static_dir = STATIC_WORKFLOWS.parent / "research_cases"
        static_dir.mkdir(parents=True, exist_ok=True)
        target = static_dir / name
        target.write_bytes(path.read_bytes())
    return path


def figure_inputs(images: Layer, dest: Path) -> Path:
    frame = images.data
    n = min(8, len(frame))
    fig, axes = plt.subplots(2, 4, figsize=(12.5, 6.4))
    for ax, (_, row) in zip(axes.ravel(), frame.head(n).iterrows()):
        path = Path(str(row["image_path"]))
        if path.is_file():
            ax.imshow(plt.imread(path))
        ax.set_axis_off()
        ax.set_title(str(row["image_id"])[:28], fontsize=7)
    fig.suptitle(
        "TCIS inputs — Wikimedia Commons, CC BY-SA 4.0 · n=8 · not a census",
        fontsize=11,
    )
    fig.text(
        0.5,
        0.02,
        f"Source: Wikimedia Commons. License: CC BY-SA 4.0. {CITATION}",
        ha="center",
        fontsize=8,
    )
    return _save(fig, dest, "tcis_inputs.png")


def figure_sampling(city, images: Layer, dest: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.2, 7.2))
    images.plot(
        ax=ax,
        context=city,
        title="Observation points on streets and buildings",
        show_scale=True,
        locator=True,
    )
    ax.set_title(CAPTION, fontsize=9)
    fig.text(
        0.5,
        0.01,
        "Spatial support: geotagged photo points. n=8 Commons photos, not a Punggol census.",
        ha="center",
        fontsize=8,
    )
    return _save(fig, dest, "tcis_sampling_context.png")


def figure_features(city, predictions: Layer, dest: Path) -> Path:
    cols = [name for name in IF_COLUMNS if name in predictions.data.columns]
    if not cols:
        cols = [name for name in ("Colorfulness", "Contrast") if name in predictions.data.columns]
    if not cols:
        raise RuntimeError("no image-feature columns available for tcis_image_features.png")
    fig, axes = plt.subplots(1, min(3, len(cols)), figsize=(12.5, 4.6))
    if min(3, len(cols)) == 1:
        axes = [axes]
    for ax, col in zip(axes, cols[:3]):
        predictions.plot(
            ax=ax,
            context=city,
            column=col,
            title=col,
            show_scale=False,
            locator=False,
        )
    fig.suptitle("TCIS initial features on observation points (n=8)", fontsize=11)
    fig.text(
        0.5,
        0.01,
        "These are model/image features, not field surveys. Empty units are not shown as 0.",
        ha="center",
        fontsize=8,
    )
    return _save(fig, dest, "tcis_image_features.png")


def figure_vpi(city, predictions: Layer, dest: Path) -> Path:
    cols = [name for name in VPI_COLUMNS if name in predictions.data.columns][:4]
    if not cols:
        raise RuntimeError("no VPI columns available")
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 9.0))
    for ax, col in zip(axes.ravel(), cols):
        predictions.plot(
            ax=ax,
            context=city,
            column=col,
            title=f"{col} (score 0–5)",
            show_scale=False,
            locator=False,
            vmin=0,
            vmax=5,
        )
    fig.suptitle("Selected VPI point maps · score 0–5 · n=8", fontsize=11)
    fig.text(
        0.5,
        0.01,
        "VPI are TCIS heads, not measured meteorology. Spatial support: photo points.",
        ha="center",
        fontsize=8,
    )
    return _save(fig, dest, "tcis_vpi.png")


def figure_vata(city, predictions: Layer, units, dest: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.8))
    predictions.plot(
        ax=axes[0],
        context=city,
        column="thermal_affordance",
        title="VATA / thermal_affordance (points)",
        vmin=0,
        vmax=5,
        show_scale=False,
        locator=True,
    )
    aggregated = uc.fusion.aggregate(
        predictions,
        units,
        stat="mean",
        column="thermal_affordance",
        indicator="thermal_affordance",
    )
    resolved = plot_indicator_frame(
        axes[1],
        aggregated.to_geopandas(indicator="thermal_affordance"),
        name="thermal_affordance",
        unit="score_0_5",
        context=city,
        alpha=0.75,
        missing_style="hatch",
        show_scale=False,
        locator=False,
    )
    colorbar(fig, axes[1], resolved)
    axes[1].set_title("Mean VATA on 250 m units (nodata hatched)")
    fig.suptitle(CAPTION, fontsize=9)
    fig.text(
        0.5,
        0.01,
        "Coverage is the 8 photo points. Unobserved units stay empty. Not a city-scale map.",
        ha="center",
        fontsize=8,
    )
    return _save(fig, dest, "tcis_thermal_affordance.png")


def figure_cross(city, predictions: Layer, units, ndvi, ndbi, utci, dest: Path) -> Path:
    vata = uc.fusion.aggregate(
        predictions, units, stat="mean", column="thermal_affordance", indicator="thermal_affordance"
    )
    ndvi_u = uc.fusion.aggregate(ndvi, units, stat="mean", indicator="ndvi")
    ndbi_u = uc.fusion.aggregate(ndbi, units, stat="mean", indicator="ndbi")
    utci_u = uc.fusion.aggregate(utci, units, stat="mean", indicator="utci")
    combined = uc.fusion.combine(units, vata, ndvi_u, ndbi_u, utci_u)
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 8.6))
    panels = [
        (axes[0, 0], "thermal_affordance", "score_0_5", "VATA (0–5)"),
        (axes[0, 1], "utci", "degree_celsius", "UTCI (°C, modelled MRT)"),
        (axes[0, 2], "ndvi", None, "NDVI"),
        (axes[1, 0], "ndbi", None, "NDBI"),
    ]
    for ax, name, unit, title in panels:
        resolved = plot_indicator_frame(
            ax,
            combined.to_geopandas(indicator=name),
            name=name,
            unit=unit,
            context=city,
            alpha=0.75,
            missing_style="hatch",
            show_scale=False,
            locator=False,
        )
        colorbar(fig, ax, resolved)
        ax.set_title(title)
    table = combined.to_pandas().pivot_table(
        index="unit_id", columns="indicator", values="value"
    )
    ax = axes[1, 1]
    if {"thermal_affordance", "utci"}.issubset(table.columns):
        sub = table.dropna(subset=["thermal_affordance", "utci"])
        ax.scatter(sub["utci"], sub["thermal_affordance"], c="#b85c38", s=36)
        if len(sub) >= 2:
            corr = float(sub["thermal_affordance"].corr(sub["utci"]))
            ax.set_title(f"VATA vs UTCI · r={corr:.2f} · correlation only")
        else:
            ax.set_title("VATA vs UTCI · correlation only")
        ax.set_xlabel("UTCI (°C)")
        ax.set_ylabel("VATA (0–5)")
    else:
        ax.set_axis_off()
    ax = axes[1, 2]
    if {"thermal_affordance", "ndvi"}.issubset(table.columns):
        sub = table.dropna(subset=["thermal_affordance", "ndvi"])
        ax.scatter(sub["ndvi"], sub["thermal_affordance"], c="#2f6d3a", s=36)
        if len(sub) >= 2:
            corr = float(sub["thermal_affordance"].corr(sub["ndvi"]))
            ax.set_title(f"VATA vs NDVI · r={corr:.2f} · correlation only")
        else:
            ax.set_title("VATA vs NDVI · correlation only")
        ax.set_xlabel("NDVI")
        ax.set_ylabel("VATA (0–5)")
    else:
        ax.set_axis_off()
    fig.suptitle(
        "Cross-domain comparison · correlation only · not causal · n=8 points on 250 m units",
        fontsize=10,
    )
    fig.text(
        0.5,
        0.01,
        "UTCI uses a modelled MRT proxy, not a measured spatial weather field. VATA ≠ UTCI.",
        ha="center",
        fontsize=8,
    )
    return _save(fig, dest, "tcis_cross_domain.png")


def main(out_dir: str | Path | None = None, mode: str = "case") -> dict:
    dest = Path(out_dir or CASE / "output")
    dest.mkdir(parents=True, exist_ok=True)
    city = load_punggol()
    units = uc.units.grid(city, cell_size=250)
    images = image_layer()
    predictions = predict_or_load(images, mode=mode)
    ndvi, ndbi, utci = heat_layers(city)
    many = uc.fusion.aggregate_many(
        predictions,
        units,
        columns={
            "thermal_affordance": {"indicator": "thermal_affordance", "unit": "score_0_5"},
            "shading_area": {"indicator": "perceived_shading", "unit": "score_0_5"},
            "greenery_rate": {"indicator": "perceived_greenery", "unit": "score_0_5"},
        },
        stat="mean",
    )
    ndvi_u = uc.fusion.aggregate(ndvi, units, stat="mean", indicator="ndvi")
    ndbi_u = uc.fusion.aggregate(ndbi, units, stat="mean", indicator="ndbi")
    utci_u = uc.fusion.aggregate(utci, units, stat="mean", indicator="utci")
    combined = uc.fusion.combine(units, many, ndvi_u, ndbi_u, utci_u)
    figures = [
        figure_inputs(images, dest),
        figure_sampling(city, images, dest),
        figure_features(city, predictions, dest),
        figure_vpi(city, predictions, dest),
        figure_vata(city, predictions, units, dest),
        figure_cross(city, predictions, units, ndvi, ndbi, utci, dest),
    ]
    table = dest / "indicator_result.csv"
    combined.to_pandas().to_csv(table, index=False)
    provenance = dest / "provenance.json"
    provenance.write_text(
        json.dumps(
            {
                "case": "thermal_comfort_in_sight",
                "n_images": int(len(images.data)),
                "citation": CITATION,
                "sample_warning": "n=8 licensed Commons photos; not a Punggol census",
                "vata": "visual thermal affordance (TCIS), not measured comfort, not UTCI",
                "utci": "pythermalcomfort UTCI with modelled NDVI/NDBI MRT proxy",
                "image_checksums": {
                    Path(path).name: sha256(Path(path))
                    for path in images.data["image_path"]
                    if Path(path).is_file()
                },
                "prediction_source": (predictions.metadata or {}).get("processing"),
                "model": (predictions.metadata or {}).get("model"),
                "urbancode_version": uc.__version__,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    for figure in figures:
        copy_to_static(figure, f"research_cases/{figure.name}")
    return {
        "result": combined,
        "images": images,
        "predictions": predictions,
        "figures": figures,
        "artifacts": [table, provenance],
        "summary": f"n={len(images.data)} mode={mode}",
    }


if __name__ == "__main__":
    print(main()["summary"])
