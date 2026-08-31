from __future__ import annotations

from pathlib import Path

from examples.recipes.network.fetch_punggol import main as network_main


def main(out_dir: str | Path) -> dict:
    out = network_main(out_dir)
    dest = Path(out_dir)
    (dest / "command.txt").write_text(
        "uc network fetch --place 'Punggol, Singapore' --layers streets --out city\n"
        "Python: uc.network.fetch(place=..., layers=['streets'])\n",
        encoding="utf-8",
    )
    return out
