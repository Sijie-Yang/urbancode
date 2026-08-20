"""Observed Open-Meteo fields + NDVI/NDBI MRT proxy → spatial UTCI."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import urbancode as uc
from urbancode.imagery.source import derived_layer, open_raster

from examples.recipes._common import climate_dir, copy_to_static, load_punggol


def main(out_dir: str | Path) -> dict:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    rows = json.loads((climate_dir() / "observations.json").read_text(encoding="utf-8"))
    row = next(item for item in rows if item["city_id"] == "punggol")
    city = load_punggol(["sentinel2"])
    ndvi = uc.imagery.ndvi(city.layers["sentinel2"])
    ndbi = uc.imagery.ndbi(city.layers["sentinel2"])
    src = open_raster(ndvi)
    tair = float(row["air_temperature_c"])
    mrt_array = tair + 6.0 * np.clip(open_raster(ndbi).array_2d, 0, 1) - 4.0 * np.clip(
        src.array_2d, 0, 1
    )
    air = derived_layer(
        "air_temperature",
        np.full(src.array_2d.shape, tair),
        src,
        processing={"op": "open_meteo_point", "status": "observed"},
        extra={"unit": "degree_celsius", "source": row["source"]},
    )
    mrt = derived_layer(
        "mean_radiant_temperature",
        mrt_array,
        src,
        processing={"op": "ndvi_ndbi_mrt_proxy", "status": "modelled"},
        extra={"unit": "degree_celsius"},
    )
    utci = uc.climate.utci(
        air_temperature=air,
        mean_radiant_temperature=mrt,
        wind_speed=float(row["wind_speed_ms"]),
        relative_humidity=float(row["relative_humidity_percent"]),
    )
    if hasattr(utci, "metadata"):
        utci.metadata["quality_flags"] = ["modelled_mrt_proxy"]
        utci.metadata["input_status"] = {
            "air_temperature": "Observed",
            "relative_humidity": "Observed",
            "wind_speed": "Observed",
            "mean_radiant_temperature": "Modelled NDVI/NDBI proxy",
        }
    figure = utci.plot(
        title=f"UTCI {row['timestamp']} UTC (MRT = Tair + 6·NDBI − 4·NDVI)",
        save=dest / "utci_real.png",
    )
    static = copy_to_static(figure, "climate/utci_real.png")
    note = dest / "inputs.txt"
    note.write_text(
        f"Observed T={tair} C RH={row['relative_humidity_percent']} "
        f"v={row['wind_speed_ms']} m/s\n"
        "Modelled MRT proxy from NDVI/NDBI\n"
        f"Source={row['source']}\n",
        encoding="utf-8",
    )
    return {
        "result": utci,
        "figures": [figure, static],
        "artifacts": [note],
        "summary": f"spatial UTCI from Open-Meteo {row['timestamp']} with MRT proxy",
        "docs_figures": {"utci_real.png": "recipes/climate/utci_real.png"},
    }
