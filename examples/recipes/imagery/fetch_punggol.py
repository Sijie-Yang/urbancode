"""Offline uc.imagery.fetch case: committed STAC window, not a live search."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol


def main(out_dir: str | Path) -> dict:
    city = load_punggol(["sentinel2"])
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    layer = city.layers["sentinel2"]
    figure = layer.plot(
        title="Committed Sentinel-2 fetch (offline)",
        save=dest / "fetch_punggol.png",
    )
    static = copy_to_static(figure, "imagery/fetch_punggol.png")
    meta = layer.metadata or {}
    note = dest / "stac.txt"
    note.write_text(
        f"item_ids={meta.get('sentinel_item_ids')}\n"
        f"datetime={meta.get('sentinel_datetime')}\n"
        f"cloud={meta.get('sentinel_cloud_cover')}\n"
        f"bands={meta.get('bands')}\n"
        "live uc.imagery.fetch is Tier 2\n",
        encoding="utf-8",
    )
    return {
        "result": layer,
        "figures": [figure, static],
        "artifacts": [note],
        "summary": f"committed item {meta.get('sentinel_item_ids')}",
        "docs_figures": {"fetch_punggol.png": "recipes/imagery/fetch_punggol.png"},
    }


if __name__ == "__main__":
    print(main(Path("examples/output/recipes/imagery/fetch_punggol"))["summary"])
