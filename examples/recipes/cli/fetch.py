"""Document uc fetch against the committed pocket (live refresh is Tier 2)."""

from __future__ import annotations

from pathlib import Path

from examples.recipes._common import copy_to_static, load_punggol


def main(out_dir: str | Path) -> dict:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    city = load_punggol(["streets", "buildings", "parks"])
    figure = city.plot(
        layers=["streets", "buildings", "parks"],
        title="Equivalent of: uc fetch --place 'Punggol, Singapore' --layers streets,buildings,parks",
        save=dest / "cli_fetch.png",
    )
    static = copy_to_static(figure, "cli/fetch.png")
    (dest / "command.txt").write_text(
        "uc fetch --place 'Punggol, Singapore' --layers streets,buildings,parks --out city\n"
        "Python: uc.fetch(place=..., layers=[...], out=...)\n"
        "This offline recipe plots the committed pocket, not a live download.\n",
        encoding="utf-8",
    )
    return {
        "result": city,
        "figures": [figure, static],
        "artifacts": [dest / "command.txt"],
        "summary": "offline uc fetch equivalent",
        "docs_figures": {"cli_fetch.png": "recipes/cli/fetch.png"},
    }
