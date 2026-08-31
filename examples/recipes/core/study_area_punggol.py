"""StudyArea.from_bbox on the Punggol pocket."""

from __future__ import annotations

from pathlib import Path

import urbancode as uc

from examples.recipes._common import copy_to_static, load_punggol


def main(out_dir: str | Path) -> dict:
    city = load_punggol(["streets"])
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    area = city.study_area
    figure = city.plot(
        layers=["streets"],
        title=f"{area.place} — {area.metric_crs} / {area.bbox}",
        save=dest / "study_area_punggol.png",
    )
    static = copy_to_static(figure, "core/study_area_punggol.png")
    note = dest / "study_area.txt"
    note.write_text(
        f"from_bbox{area.bbox}\nplace={area.place}\ncity_id={area.city_id}\n"
        f"geographic_crs={area.geographic_crs}\nmetric_crs={area.metric_crs}\n",
        encoding="utf-8",
    )
    return {
        "result": area,
        "figures": [figure, static],
        "artifacts": [note],
        "summary": f"{area.city_id} {area.metric_crs}",
        "docs_figures": {"study_area_punggol.png": "recipes/core/study_area_punggol.png"},
    }
