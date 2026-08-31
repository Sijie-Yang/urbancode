"""uc.imagery.read on the committed Sentinel-2 window."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol


def main(out_dir: str | Path) -> dict:
    city = load_punggol(["sentinel2"])
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    layer = uc.imagery.read(city.layers["sentinel2"].path, name="sentinel2")
    figure = layer.plot(title="Punggol Sentinel-2 window", save=dest / "read_punggol.png")
    static = copy_to_static(figure, "imagery/read_punggol.png")
    meta = dest / "raster_metadata.txt"
    meta.write_text(
        f"crs={layer.crs}\nbands={layer.metadata.get('bands')}\n"
        f"bounds={layer.metadata.get('bounds')}\n"
        f"resolution={layer.metadata.get('resolution')}\n",
        encoding="utf-8",
    )
    return {
        "result": layer,
        "figures": [figure, static],
        "artifacts": [meta],
        "summary": f"read {layer.metadata.get('bands')}",
        "docs_figures": {"read_punggol.png": "recipes/imagery/read_punggol.png"},
    }


if __name__ == "__main__":
    print(main(Path("examples/output/recipes/imagery/read_punggol"))["summary"])
