"""Shared NDVI / NDWI / NDBI panel for the Punggol Sentinel-2 window."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol


def run_indices(out_dir: str | Path) -> dict:
    city = load_punggol(["sentinel2"])
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    source = city.layers["sentinel2"]
    ndvi = uc.imagery.ndvi(source)
    try:
        ndwi = uc.imagery.ndwi(source)
    except Exception as exc:
        raise RuntimeError(
            "NDWI needs B03. Rebuild the real pocket with "
            "scripts/data/build_real_pockets.py --city punggol"
        ) from exc
    ndbi = uc.imagery.ndbi(source)
    paths = {
        "NDVI": dest / "ndvi.png",
        "NDWI": dest / "ndwi.png",
        "NDBI": dest / "ndbi.png",
    }
    ndvi.plot(title="NDVI", save=paths["NDVI"])
    ndwi.plot(title="NDWI", save=paths["NDWI"])
    ndbi.plot(title="NDBI", save=paths["NDBI"])
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, (title, path) in zip(axes, paths.items()):
        ax.imshow(plt.imread(path))
        ax.set_axis_off()
        ax.set_title(title)
    fig.suptitle("Punggol Sentinel-2 indices (single date)")
    panel = dest / "indices_punggol.png"
    fig.savefig(panel, dpi=120, bbox_inches="tight")
    plt.close(fig)
    static = copy_to_static(panel, "imagery/indices_punggol.png")
    return {
        "result": {"ndvi": ndvi, "ndwi": ndwi, "ndbi": ndbi},
        "figures": [panel, static],
        "artifacts": list(paths.values()),
        "summary": "NDVI / NDWI / NDBI triple",
        "docs_figures": {"indices_punggol.png": "recipes/imagery/indices_punggol.png"},
    }
