"""Local clustering on the Punggol walk graph."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol


def main(out_dir: str | Path) -> dict:
    city = load_punggol(["streets"])
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    layer = uc.network.clustering(city["streets"])
    mapped = dest / "clustering_map.png"
    layer.plot(title="Local clustering", save=mapped, column="clustering")
    values = np.array(list(dict(layer.data.nodes(data="clustering")).values()), dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    axes[0].imshow(plt.imread(mapped))
    axes[0].set_axis_off()
    axes[0].set_title("Map")
    axes[1].hist(values[~np.isnan(values)], bins=20, color="#4a4a4a")
    axes[1].set_title("Many 0s: degree 1–2 street nodes")
    axes[1].set_xlabel("clustering")
    panel = dest / "clustering_punggol.png"
    fig.savefig(panel, dpi=120, bbox_inches="tight")
    plt.close(fig)
    static = copy_to_static(panel, "network/clustering_punggol.png")
    return {
        "result": layer,
        "figures": [panel, static],
        "artifacts": [mapped],
        "summary": f"clustering n={len(values)} zeros={int(np.nansum(values == 0))}",
        "docs_figures": {"clustering_punggol.png": "recipes/network/clustering_punggol.png"},
    }


if __name__ == "__main__":
    print(main(Path("examples/output/recipes/network/clustering_punggol"))["summary"])
