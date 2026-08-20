"""Local efficiency on the Punggol walk graph."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol


def main(out_dir: str | Path) -> dict:
    city = load_punggol(["streets"])
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    layer = uc.network.local_efficiency(city["streets"])
    figure = layer.plot(
        title="Local efficiency (not clustering)",
        save=dest / "local_efficiency_punggol.png",
        column="local_efficiency",
    )
    static = copy_to_static(figure, "network/local_efficiency_punggol.png")
    return {
        "result": layer,
        "figures": [figure, static],
        "artifacts": [],
        "summary": "local efficiency map",
        "docs_figures": {
            "local_efficiency_punggol.png": "recipes/network/local_efficiency_punggol.png"
        },
    }


if __name__ == "__main__":
    print(main(Path("examples/output/recipes/network/local_efficiency_punggol"))["summary"])
