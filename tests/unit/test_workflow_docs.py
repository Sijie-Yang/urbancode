from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / "examples" / "workflows"
DOCS = ROOT / "docs" / "source" / "workflows"

SCRIPTS = (
    "punggol_end_to_end.py",
    "climate_heat_stress.py",
    "streetview_to_grid.py",
    "multi_city_contract.py",
    "green_accessibility.py",
    "real_heat_stress.py",
    "real_multi_city.py",
    "street_experience.py",
)


def test_workflow_scripts_exist() -> None:
    for name in SCRIPTS:
        assert (WORKFLOWS / name).is_file()


def test_workflow_literalincludes_exist() -> None:
    missing: list[str] = []
    for path in DOCS.glob("*.rst"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if "literalinclude::" not in line:
                continue
            rel = line.split("literalinclude::", 1)[1].strip()
            target = (path.parent / rel).resolve()
            if not target.is_file():
                missing.append(f"{path.name} -> {rel}")
    assert missing == []
