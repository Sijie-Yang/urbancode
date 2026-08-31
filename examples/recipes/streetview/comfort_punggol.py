"""TCIS comfort on a licensed photo. Offline uses committed scores when present."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from examples.recipes._common import copy_to_static
from examples.recipes.streetview._precomputed import load_or_run, photo_path


def _run(photo: Path) -> dict:
    import urbancode as uc

    table = uc.svi.comfort(str(photo.parent), output_filename=None)
    row = table.iloc[0].to_dict() if hasattr(table, "iloc") else dict(table)
    return {"photo": photo.name, "scores": {k: row[k] for k in row}}


def main(out_dir: str | Path) -> dict:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    photo = photo_path()
    try:
        payload = load_or_run("comfort", _run)
    except Exception as exc:
        raise RuntimeError(
            "comfort recipe needs urbancode[svi] or "
            "examples/data/real/streetview/precomputed/comfort.json"
        ) from exc
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].imshow(plt.imread(photo))
    axes[0].set_axis_off()
    axes[0].set_title(photo.name)
    text = "\n".join(f"{k}: {v}" for k, v in list((payload.get("scores") or {}).items())[:12])
    axes[1].axis("off")
    axes[1].text(0.05, 0.5, text or "precomputed TCIS scores", va="center", fontsize=9)
    figure = dest / "comfort_punggol.png"
    fig.savefig(figure, dpi=120, bbox_inches="tight")
    plt.close(fig)
    static = copy_to_static(figure, "streetview/comfort_punggol.png")
    (dest / "comfort.json").write_text(
        __import__("json").dumps(payload, indent=2, default=str), encoding="utf-8"
    )
    return {
        "result": payload,
        "figures": [figure, static],
        "artifacts": [dest / "comfort.json"],
        "summary": f"comfort for {photo.name}",
        "docs_figures": {"comfort_punggol.png": "recipes/streetview/comfort_punggol.png"},
    }
