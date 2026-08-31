"""Map streets and building footprints in the Punggol extract."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

DATA = Path(__file__).resolve().parents[1] / "data" / "real" / "punggol"


def main(out_dir: str | Path, *, add_basemap: bool = False) -> dict[str, Path]:
    city = uc.load(DATA)
    figure = city.plot(
        layers=["streets", "buildings"],
        title="Punggol, Singapore — streets and buildings",
        save=Path(out_dir) / "01_streets_buildings.png",
        basemap=add_basemap,
    )
    return {"figure": figure}


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
