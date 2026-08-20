#!/usr/bin/env python3
"""Four-stage spatial-support diagram for the Concepts page."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "source" / "_static" / "concepts" / "native_to_fusion.png"


def main() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10.5, 3.2))
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 3.2)
    ax.axis("off")
    boxes = (
        (0.3, "street / building\nraster / point", "#deebf7"),
        (2.9, "native\nindicator", "#c7e9c0"),
        (5.5, "common\nAnalysisUnits", "#fee6ce"),
        (8.1, "fusion\nresult", "#fde0dd"),
    )
    for x, text, color in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, 0.9),
                2.0,
                1.4,
                boxstyle="round,pad=0.04,rounding_size=0.12",
                facecolor=color,
                edgecolor="#444444",
                linewidth=1.0,
            )
        )
        ax.text(x + 1.0, 1.6, text, ha="center", va="center", fontsize=10)
    for x in (2.35, 4.95, 7.55):
        ax.add_patch(
            FancyArrowPatch(
                (x, 1.6),
                (x + 0.5, 1.6),
                arrowstyle="-|>",
                mutation_scale=12,
                color="#333333",
            )
        )
    ax.set_title("Native geometry → domain analysis → common units → fusion", loc="left")
    fig.tight_layout()
    fig.savefig(OUT, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return OUT


if __name__ == "__main__":
    print(main())
