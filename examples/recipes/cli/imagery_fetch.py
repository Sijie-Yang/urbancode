from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def main(out_dir: str | Path) -> dict:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    src = ROOT / "docs" / "source" / "_static" / "recipes" / "imagery" / "fetch_punggol.png"
    if not src.exists():
        raise FileNotFoundError(src)
    figure = dest / "cli_imagery_fetch.png"
    figure.write_bytes(src.read_bytes())
    static = (
        ROOT / "docs" / "source" / "_static" / "recipes" / "cli" / "imagery_fetch.png"
    )
    static.parent.mkdir(parents=True, exist_ok=True)
    static.write_bytes(src.read_bytes())
    (dest / "command.txt").write_text(
        "uc imagery fetch --place 'Punggol, Singapore' --layers sentinel2 --out city\n"
        "Python: uc.imagery.fetch(place=..., layers=['sentinel2'])\n"
        "Offline figure is the committed STAC window, not a live download.\n",
        encoding="utf-8",
    )
    return {
        "result": "uc imagery fetch",
        "figures": [figure, static],
        "artifacts": [dest / "command.txt"],
        "summary": "offline uc imagery fetch equivalent",
        "docs_figures": {"cli_imagery_fetch.png": "recipes/cli/imagery_fetch.png"},
    }
