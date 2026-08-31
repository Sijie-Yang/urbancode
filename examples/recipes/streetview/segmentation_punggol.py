from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from examples.recipes._common import copy_to_static
from examples.recipes.streetview._precomputed import load_or_run, photo_path


def _run(photo: Path) -> dict:
    import urbancode as uc

    result = uc.svi.segmentation(str(photo))
    if hasattr(result, "to_dict"):
        return result.to_dict()
    return {"result": str(type(result)), "repr": str(result)[:500]}


def main(out_dir: str | Path) -> dict:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    photo = photo_path()
    payload = load_or_run("segmentation", _run)
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].imshow(plt.imread(photo))
    axes[0].set_axis_off()
    axes[0].set_title("source")
    axes[1].axis("off")
    axes[1].text(0.05, 0.5, str(payload)[:600], va="center", fontsize=8)
    figure = dest / "segmentation_punggol.png"
    fig.savefig(figure, dpi=120, bbox_inches="tight")
    plt.close(fig)
    static = copy_to_static(figure, "streetview/segmentation_punggol.png")
    return {
        "result": payload,
        "figures": [figure, static],
        "artifacts": [],
        "summary": "segmentation panel",
        "docs_figures": {
            "segmentation_punggol.png": "recipes/streetview/segmentation_punggol.png"
        },
    }
