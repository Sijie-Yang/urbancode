"""Betweenness and closeness on the Punggol walk graph."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol


def main(out_dir: str | Path) -> dict:
    city = load_punggol(["streets"])
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    between = uc.network.centrality(city["streets"], metric="betweenness")
    close = uc.network.centrality(city["streets"], metric="closeness")
    left = dest / "betweenness.png"
    right = dest / "closeness.png"
    between.plot(title="Betweenness (boundary-sensitive)", save=left, column="betweenness")
    close.plot(title="Closeness", save=right, column="closeness")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    for ax, path, title in (
        (axes[0], left, "Betweenness"),
        (axes[1], right, "Closeness"),
    ):
        ax.imshow(plt.imread(path))
        ax.set_axis_off()
        ax.set_title(title)
    fig.suptitle("Punggol walk graph centrality")
    panel = dest / "centrality_punggol.png"
    fig.savefig(panel, dpi=120, bbox_inches="tight")
    plt.close(fig)
    static = copy_to_static(panel, "network/centrality_punggol.png")
    return {
        "result": {"betweenness": between, "closeness": close},
        "figures": [panel, static],
        "artifacts": [left, right],
        "summary": "betweenness + closeness on the Punggol walk graph",
        "docs_figures": {"centrality_punggol.png": "recipes/network/centrality_punggol.png"},
    }


if __name__ == "__main__":
    print(main(Path("examples/output/recipes/network/centrality_punggol"))["summary"])
