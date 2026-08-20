"""City.load, plot, to_dir, from_dir, Layer.save."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol, pocket


def main(out_dir: str | Path) -> dict:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    city = load_punggol(["streets", "parks"])
    city.add_layer(
        "study_note",
        __import__("pandas").DataFrame({"note": ["round-trip"]}),
        kind="table",
        source="recipe",
    )
    figure = city.plot(
        layers=["streets", "parks"],
        title="Punggol City layer inventory",
        save=dest / "city_roundtrip_punggol.png",
    )
    static = copy_to_static(figure, "core/city_roundtrip_punggol.png")
    saved = city.to_dir(dest / "city", overwrite=True)
    reloaded = uc.City.from_dir(saved, lazy=True)
    layer_png = dest / "parks_layer.png"
    reloaded.layer("parks").plot(title="Layer.plot after from_dir", save=layer_png)
    tree = dest / "city_tree.txt"
    tree.write_text(
        "\n".join(sorted(p.relative_to(saved).as_posix() for p in saved.rglob("*") if p.is_file()))
        + "\n",
        encoding="utf-8",
    )
    return {
        "result": reloaded,
        "figures": [figure, static],
        "artifacts": [saved, tree, layer_png],
        "summary": f"layers={list(reloaded.keys())} source={pocket('punggol')}",
        "docs_figures": {"city_roundtrip_punggol.png": "recipes/core/city_roundtrip_punggol.png"},
    }
