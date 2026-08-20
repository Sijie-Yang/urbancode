"""Offline stand-in for uc.fetch: plot the committed Punggol City layout."""

from __future__ import annotations

from pathlib import Path

from examples.recipes._common import copy_to_static, load_punggol


def main(out_dir: str | Path) -> dict:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    city = load_punggol(["streets", "buildings", "parks"])
    figure = city.plot(
        layers=["streets", "buildings", "parks"],
        title="Punggol pocket — City layout written by uc.fetch (offline fixture)",
        save=dest / "fetch_punggol.png",
    )
    static = copy_to_static(figure, "cli/fetch.png")
    note = dest / "fetch.txt"
    note.write_text(
        "Live: uc.fetch(place='Punggol, Singapore', layers=['streets','buildings','parks'])\n"
        "This recipe plots examples/data/real/punggol, not a live Overpass/STAC call.\n",
        encoding="utf-8",
    )
    return {
        "result": city,
        "figures": [figure, static],
        "artifacts": [note],
        "summary": "offline uc.fetch equivalent",
        "docs_figures": {"fetch_punggol.png": "recipes/cli/fetch.png"},
    }
