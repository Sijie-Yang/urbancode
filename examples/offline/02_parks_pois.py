"""Map parks and points of interest in the Punggol extract."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

DATA = Path(__file__).resolve().parents[1] / "data" / "real" / "punggol"


def main(out_dir: str | Path, *, add_basemap: bool = False) -> dict[str, Path]:
    city = uc.load(DATA)
    figure = city.plot(
        layers=["parks", "pois"],
        title="Punggol, Singapore — parks and POIs",
        save=Path(out_dir) / "02_parks_pois.png",
        basemap=add_basemap,
    )
    return {"figure": figure}


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
