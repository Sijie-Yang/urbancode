"""Betweenness on the Punggol street graph."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

DATA = Path(__file__).resolve().parents[1] / "data" / "real" / "punggol"


def main(out_dir: str | Path, *, add_basemap: bool = False) -> dict[str, Path]:
    city = uc.load(DATA)
    result = uc.network.centrality(
        city["streets"],
        metric="betweenness",
        radius=500,
    )
    figure = result.plot(
        title="Punggol, Singapore — betweenness",
        save=Path(out_dir) / "06_access.png",
    )
    del add_basemap
    return {"figure": figure}


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
