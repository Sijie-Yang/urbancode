"""Show a real street-level photo and committed comfort metadata.

This does not run TCIS inference. Live prediction is
examples/live/03_streetview_predict.py.
"""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

# Archived single-photo City (streetview.jpg + comfort.csv). New SVI
# teaching uses examples/data/real/streetview and street_experience.py.
DATA = Path(__file__).resolve().parents[1] / "data" / "punggol_pocket"


def main(out_dir: str | Path, *, add_basemap: bool = False) -> dict[str, Path]:
    city = uc.load(DATA)
    figure = city.plot(
        layers=["streetview", "comfort"],
        title="Punggol, Singapore",
        save=Path(out_dir) / "07_streetview_results.png",
    )
    del add_basemap
    return {"figure": figure}


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
