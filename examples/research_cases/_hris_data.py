"""Load committed Heat Resilience in Sight summary tables only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "examples" / "data" / "research_cases" / "heat_resilience_in_sight"
CITATION = (
    "Yang, S. et al. Heat Resilience in Sight: Climate-Conditioned Thermal "
    "Affordance of Streetscapes Across Cities and Seasons. Workshop draft. "
    "https://github.com/Sijie-Yang/Heat-Resilience-In-Sight"
)
SINGAPORE_N = 21772
TCIS_SINGAPORE_N = 92233
D_REF = 7.991
V_REF = 1.732
CITY_ORDER = (
    "svi_sg",
    "svi_hk",
    "svi_tokyo",
    "svi_ny",
    "svi_melbourne",
    "svi_jh",
    "svi_rio",
    "svi_capetown",
)


def load_manifest() -> dict:
    return json.loads((CASE / "manifest.json").read_text(encoding="utf-8"))


def load_calibration() -> dict:
    return json.loads((CASE / "calibration.json").read_text(encoding="utf-8"))


def load_city_stats() -> pd.DataFrame:
    return pd.read_csv(CASE / "city_vata_stats.csv")


def load_annual() -> pd.DataFrame:
    return pd.read_csv(CASE / "annual_climate_vata.csv")


def load_monthly() -> pd.DataFrame:
    return pd.read_csv(CASE / "monthly_climate_vata.csv")


def load_robustness_summary() -> pd.DataFrame:
    return pd.read_csv(CASE / "robustness_summary.csv")


def load_sign_stability() -> pd.DataFrame:
    return pd.read_csv(CASE / "robustness_sign_stability.csv")


def load_domain_shift() -> pd.DataFrame:
    return pd.read_csv(CASE / "domain_shift.csv")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
