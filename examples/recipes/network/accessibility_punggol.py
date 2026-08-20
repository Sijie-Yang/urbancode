"""Network reachability at 150 m and 500 m. Not population accessibility."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol


def main(out_dir: str | Path) -> dict:
    city = load_punggol(["streets"])
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    near = uc.network.accessibility(city["streets"], radius=150, metric="reachability")
    far = uc.network.accessibility(city["streets"], radius=500, metric="reachability")
    a = dest / "reach_150.png"
    b = dest / "reach_500.png"
    near.plot(title="Reachable nodes within 150 m", save=a, column="reachability")
    far.plot(title="Reachable nodes within 500 m", save=b, column="reachability")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    for ax, path, title in ((axes[0], a, "150 m"), (axes[1], b, "500 m")):
        ax.imshow(plt.imread(path))
        ax.set_axis_off()
        ax.set_title(title)
    fig.suptitle("Punggol network reachability (node count, not jobs/population)")
    panel = dest / "accessibility_punggol.png"
    fig.savefig(panel, dpi=120, bbox_inches="tight")
    plt.close(fig)
    static = copy_to_static(panel, "network/accessibility_punggol.png")
    return {
        "result": {"r150": near, "r500": far},
        "figures": [panel, static],
        "artifacts": [a, b],
        "summary": "reachability 150 m vs 500 m",
        "docs_figures": {"accessibility_punggol.png": "recipes/network/accessibility_punggol.png"},
    }


if __name__ == "__main__":
    print(main(Path("examples/output/recipes/network/accessibility_punggol"))["summary"])
