"""uc --version terminal output."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

import urbancode as uc

from examples.recipes._common import copy_to_static


def main(out_dir: str | Path) -> dict:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    text = f"urbancode {uc.__version__}"
    (dest / "version.txt").write_text(text + "\n", encoding="utf-8")
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.axis("off")
    ax.text(0.05, 0.5, f"$ uc --version\n{text}", va="center", family="monospace", fontsize=14)
    figure = dest / "version.png"
    fig.savefig(figure, dpi=120, bbox_inches="tight")
    plt.close(fig)
    static = copy_to_static(figure, "cli/version.png")
    return {
        "result": text,
        "figures": [figure, static],
        "artifacts": [dest / "version.txt"],
        "summary": text,
        "docs_figures": {"version.png": "recipes/cli/version.png"},
    }
