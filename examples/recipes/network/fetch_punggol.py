"""Offline case for uc.network.fetch: the committed Punggol street graph."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol


def main(out_dir: str | Path) -> dict:
    city = load_punggol(["streets"])
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    figure = city.plot(
        layers=["streets"],
        title="Punggol pocket — OSM walk network",
        save=dest / "fetch_punggol.png",
    )
    static = copy_to_static(figure, "network/fetch_punggol.png")
    graph = city["streets"]
    summary = f"nodes={graph.number_of_nodes()} edges={graph.number_of_edges()} type=walk"
    (dest / "summary.txt").write_text(summary + "\n", encoding="utf-8")
    return {
        "result": city,
        "figures": [figure, static],
        "artifacts": [dest / "summary.txt"],
        "summary": summary,
        "docs_figures": {"fetch_punggol.png": "recipes/network/fetch_punggol.png"},
    }


if __name__ == "__main__":
    print(main(Path("examples/output/recipes/network/fetch_punggol"))["summary"])
