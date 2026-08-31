from __future__ import annotations

from pathlib import Path

from examples.recipes.streetview.comfort_punggol import main as comfort_main


def main(out_dir: str | Path) -> dict:
    out = comfort_main(out_dir)
    dest = Path(out_dir)
    (dest / "command.txt").write_text(
        "uc streetview comfort path/to.jpg --out comfort.csv\n"
        "Python: uc.svi.comfort(...)\n",
        encoding="utf-8",
    )
    return out
