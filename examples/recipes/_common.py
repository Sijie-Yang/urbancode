"""Shared helpers for offline recipes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REAL = ROOT / "examples" / "data" / "real"
LEGACY_PUNGGOL = ROOT / "examples" / "data" / "punggol_pocket"
STATIC_RECIPES = ROOT / "docs" / "source" / "_static" / "recipes"
STATIC_WORKFLOWS = ROOT / "docs" / "source" / "_static" / "workflows"


def pocket(name: str = "punggol") -> Path:
    """Return the canonical real pocket under ``examples/data/real/``."""
    path = REAL / name
    if (path / "manifest.json").is_file():
        return path
    raise FileNotFoundError(
        f"no registered dataset for {name!r}; expected {path}. "
        "examples/data/punggol_pocket is archived."
    )


def streetview_dir() -> Path:
    for path in (
        REAL / "streetview" / "punggol",
        REAL / "streetview",
        LEGACY_PUNGGOL / "layers",
        pocket("punggol") / "layers",
    ):
        if path.is_dir() and any(path.glob("*.jpg")):
            return path
    raise FileNotFoundError("no street-view image directory")


def climate_dir() -> Path:
    path = REAL / "climate"
    if (path / "manifest.json").is_file():
        return path
    raise FileNotFoundError("no real climate dataset")


def save_fig(path: Path, figure: Any) -> Path:
    path = Path(figure) if figure is not None and Path(str(figure)).is_file() else path
    return Path(path)


def copy_workflow_static(src: Path, name: str) -> Path:
    dest = STATIC_WORKFLOWS / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(Path(src).read_bytes())
    return dest


def copy_to_static(src: Path, rel: str) -> Path:
    dest = STATIC_RECIPES / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(Path(src).read_bytes())
    return dest


def study_area(city, city_id: str):
    import urbancode as uc

    bbox = city.metadata.get("bbox") or (
        city.study_area.bbox if getattr(city, "study_area", None) else None
    )
    if bbox is None:
        raise ValueError("city has no bbox")
    area = uc.StudyArea.from_bbox(*bbox, place=city.place, city_id=city_id)
    city.study_area = area
    return area


def load_pocket(name: str = "punggol", layers: list[str] | None = None):
    import urbancode as uc
    from urbancode.cartography import attach_locator

    root = pocket(name)
    city = uc.load(root, layers=layers, lazy=True)
    study_area(city, name)
    attach_locator(city, root)
    return city


def load_punggol(layers: list[str] | None = None):
    return load_pocket("punggol", layers=layers)


def finish(out_dir, figures: dict[str, Path], artifacts: list | None = None, **extra) -> dict:
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    docs_figures = {}
    copied = []
    for name, src in figures.items():
        src = Path(src)
        rel = extra.pop("docs_rel", None)
        if rel is None:
            # map dest name to catalog figure path when provided
            mapped = extra.get("figure_map", {}).get(name)
            rel = mapped or f"{src.parent.name}/{src.name}"
        copied.append(copy_to_static(src, rel))
        docs_figures[src.name] = f"recipes/{rel}"
    extra.pop("figure_map", None)
    return {
        "result": extra.pop("result", None),
        "figures": list(figures.values()),
        "artifacts": artifacts or [],
        "summary": extra.pop("summary", ""),
        "docs_figures": docs_figures,
        **extra,
    }
