"""Catalog the street-view image folder."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

import urbancode as uc

from examples.recipes._common import copy_to_static, streetview_dir


def main(out_dir: str | Path) -> dict:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    folder = streetview_dir()
    catalog = uc.svi.filename(str(folder))
    catalog.to_csv(dest / "catalog.csv", index=False)
    images = list(folder.glob("*.jpg"))[:6]
    n = max(len(images), 1)
    fig, axes = plt.subplots(1, n, figsize=(3 * n, 3))
    if n == 1:
        axes = [axes]
    for ax, path in zip(axes, images):
        ax.imshow(plt.imread(path))
        ax.set_axis_off()
        ax.set_title(path.name, fontsize=8)
    fig.suptitle("Street-view catalog")
    figure = dest / "filename_punggol.png"
    fig.savefig(figure, dpi=120, bbox_inches="tight")
    plt.close(fig)
    static = copy_to_static(figure, "streetview/filename_punggol.png")
    return {
        "result": catalog,
        "figures": [figure, static],
        "artifacts": [dest / "catalog.csv"],
        "summary": f"{len(catalog)} files in {folder}",
        "docs_figures": {"filename_punggol.png": "recipes/streetview/filename_punggol.png"},
    }
