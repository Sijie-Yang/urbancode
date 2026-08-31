"""Load the licensed TCIS case catalog. Photos stay in the streetview fixture."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
STREETVIEW = ROOT / "examples" / "data" / "real" / "streetview"
CASE = ROOT / "examples" / "data" / "research_cases" / "thermal_comfort_in_sight"
CITATION = (
    "Yang, S. et al. (2024). Thermal Comfort in Sight: Thermal Affordance "
    "and its Visual Assessment for Sustainable Streetscape Design. "
    "https://arxiv.org/abs/2410.11887"
)


def punggol_catalog() -> pd.DataFrame:
    rows = json.loads((STREETVIEW / "catalog.json").read_text(encoding="utf-8"))
    frame = pd.DataFrame([row for row in rows if row.get("city_id") == "punggol"])
    if frame.empty:
        raise FileNotFoundError("no licensed Punggol street photos in the catalog")
    frame = frame.copy()
    frame["image_path"] = [str(STREETVIEW / path) for path in frame["path"]]
    frame["image_uri"] = frame["source_url"]
    frame["captured_at"] = frame.get("capture_time")
    frame["location_quality"] = frame.get("location_accuracy")
    frame["citation"] = CITATION
    return frame


def tiny_catalog() -> pd.DataFrame:
    frame = punggol_catalog().head(2).copy()
    return frame


def predictions_path() -> Path:
    return CASE / "predictions.csv"


def load_predictions() -> pd.DataFrame | None:
    path = predictions_path()
    if not path.is_file():
        return None
    return pd.read_csv(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
