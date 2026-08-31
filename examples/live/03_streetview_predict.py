"""Live TCIS comfort prediction. Run manually with urbancode[perception].

The offline gallery (examples/offline/07_streetview_results.py) only
displays precomputed scores and does not call comfort().
"""

from __future__ import annotations

from pathlib import Path

PHOTO_DIR = (
    Path(__file__).resolve().parents[1] / "data" / "real" / "streetview" / "punggol"
)


def main(out_dir: str | Path, *, add_basemap: bool = False) -> dict[str, Path]:
    import urbancode as uc

    image = next(PHOTO_DIR.glob("*.jpg"))
    scores = uc.svi.comfort(str(image), mode="image")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "comfort.csv"
    scores.to_csv(dest, index=False)
    del add_basemap
    return {"table": dest}


if __name__ == "__main__":
    print(main(Path(__file__).resolve().parents[1] / "output"))
