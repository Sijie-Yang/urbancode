"""Live TCIS comfort prediction. Run manually or under the [streetview] extra.

The offline gallery (examples/offline/07_streetview_results.py) only
displays precomputed scores and does not call comfort().
"""

from __future__ import annotations

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "punggol_pocket"


def main(out_dir: str | Path, *, add_basemap: bool = False) -> dict[str, Path]:
    import urbancode as uc

    city = uc.City.from_dir(DATA_DIR)
    image = Path(city.layer("streetview").path)
    scores = uc.streetview.comfort(str(image), mode="image")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "03_streetview_predict.csv"
    scores.to_csv(dest, index=False)
    del add_basemap
    return {"table": dest}


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
