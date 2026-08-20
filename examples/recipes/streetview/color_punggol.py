"""Colorfulness on licensed street photos."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

import urbancode as uc

from examples.recipes._common import copy_to_static, streetview_dir


def main(out_dir: str | Path) -> dict:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    folder = streetview_dir()
    catalog = uc.streetview.filename(str(folder))
    features = uc.streetview.color(catalog, folder_path=str(folder))
    features.to_csv(dest / "color.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    first = folder / str(features["Filename"].iloc[0])
    axes[0].imshow(plt.imread(first))
    axes[0].set_axis_off()
    axes[0].set_title(features["Filename"].iloc[0])
    axes[1].hist(features["Colorfulness"], bins=min(10, max(len(features), 1)), color="#2c7fb8")
    axes[1].set_title("Colorfulness")
    figure = dest / "color_punggol.png"
    fig.savefig(figure, dpi=120, bbox_inches="tight")
    plt.close(fig)
    static = copy_to_static(figure, "streetview/color_punggol.png")
    return {
        "result": features,
        "figures": [figure, static],
        "artifacts": [dest / "color.csv"],
        "summary": f"colorfulness mean={float(features['Colorfulness'].mean()):.3f}",
        "docs_figures": {"color_punggol.png": "recipes/streetview/color_punggol.png"},
    }
