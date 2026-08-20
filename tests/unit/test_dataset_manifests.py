from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_lib import CONTRACTS, REAL_DATA  # noqa: E402
from data.dataset_manifest import (  # noqa: E402
    iter_dataset_dirs,
    validate_contract,
    validate_real,
)


def test_real_datasets_are_not_synthetic() -> None:
    if not REAL_DATA.is_dir():
        return
    errors: list[str] = []
    for path in iter_dataset_dirs(REAL_DATA):
        errors.extend(validate_real(path))
    assert errors == []


def test_contract_datasets_are_synthetic() -> None:
    if not CONTRACTS.is_dir():
        return
    errors: list[str] = []
    for path in iter_dataset_dirs(CONTRACTS):
        errors.extend(validate_contract(path))
    assert errors == []


def test_no_synthetic_under_real() -> None:
    if not REAL_DATA.is_dir():
        return
    for path in REAL_DATA.rglob("manifest.json"):
        text = path.read_text(encoding="utf-8")
        assert '"synthetic": true' not in text
