from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest
import yaml

import urbancode as uc
from urbancode.errors import MissingExtraError

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "source"
MIGRATION = DOCS / "migration"
FORBIDDEN = (
    "uc.svi",
    "uc svi",
    "urbancode[svi]",
    "svi_results",
    "svi_photo",
    "uc.imagery.lst",
    "uc.streetview.places",
    "uc.network.download",
    "uc.indicators.load",
)
DELETED_TREES = (
    DOCS / "tutorials",
    DOCS / "user_guide",
    DOCS / "gallery",
    DOCS / "api",
    DOCS / "architecture",
)
UC_NAME = re.compile(r"uc\.[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+")


def _rst_files() -> list[Path]:
    return sorted(DOCS.rglob("*.rst"))


def test_old_doc_trees_are_gone() -> None:
    for path in DELETED_TREES:
        assert not path.exists(), path
    assert not (DOCS / "installation.rst").exists()
    assert not (DOCS / "quickstart.rst").exists()
    assert not (DOCS / "catalog" / "capabilities.rst").exists()
    assert not list(DOCS.glob("gallery/*.rst"))


def test_docs_do_not_teach_legacy_or_stale_names() -> None:
    hits: list[str] = []
    for path in _rst_files():
        if MIGRATION in path.parents or path.parent == MIGRATION:
            continue
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            if token == "uc.network.download":
                if re.search(r"uc\.network\.download(?!_)", text):
                    hits.append(f"{path.relative_to(ROOT)}: {token}")
                continue
            if token in text:
                hits.append(f"{path.relative_to(ROOT)}: {token}")
    assert hits == []


def test_documented_uc_names_exist() -> None:
    missing: list[str] = []
    seen: set[str] = set()
    for path in _rst_files():
        if MIGRATION in path.parents or path.parent == MIGRATION:
            continue
        for match in UC_NAME.findall(path.read_text(encoding="utf-8")):
            if match in seen:
                continue
            seen.add(match)
            obj: object = uc
            try:
                for part in match.split(".")[1:]:
                    obj = getattr(obj, part)
            except (MissingExtraError, ModuleNotFoundError, ImportError):
                continue
            except AttributeError:
                missing.append(f"{path.relative_to(ROOT)}: {match}")
    assert missing == []


def test_literalincludes_exist() -> None:
    missing: list[str] = []
    for path in _rst_files():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "literalinclude::" not in line:
                continue
            rel = line.split("literalinclude::", 1)[1].strip()
            target = (path.parent / rel).resolve()
            if not target.is_file():
                missing.append(f"{path.name} -> {rel}")
    assert missing == []


REDIRECT_DOCS = {
    "workflows/punggol_end_to_end",
    "workflows/climate_heat_stress",
    "workflows/real_heat_stress",
    "workflows/streetview_to_grid",
    "workflows/multi_city_contract",
    "workflows/real_multi_city",
}


def test_no_orphan_rst() -> None:
    listed = _toctree_docs(DOCS / "index.rst")
    listed.add("index")
    orphans: list[str] = []
    for path in _rst_files():
        doc = str(path.relative_to(DOCS)).replace("\\", "/").removesuffix(".rst")
        if doc in REDIRECT_DOCS:
            continue
        if doc not in listed:
            orphans.append(doc)
    assert orphans == []


def test_workflow_sidebar_has_only_five_canonical_titles() -> None:
    html = ROOT / "docs" / "build" / "html" / "workflows" / "index.html"
    if not html.is_file():
        pytest.skip("Sphinx HTML not built")
    text = html.read_text(encoding="utf-8")
    assert "Previous titles" not in text
    for title in (
        "Punggol end-to-end",
        "Climate heat stress",
        "Real heat stress",
        "Street view to grid",
        "Multi-city contract",
        "Real multi-city",
    ):
        assert title not in text
    for title in (
        "Punggol urban profile",
        "Green accessibility",
        "Heat exposure",
        "Street experience",
        "Multi-city comparison",
    ):
        assert title in text


def _toctree_docs(
    index: Path,
    seen: set[str] | None = None,
    visited: set[Path] | None = None,
) -> set[str]:
    docs = seen if seen is not None else set()
    visited = visited if visited is not None else set()
    resolved = index.resolve()
    if resolved in visited:
        return docs
    visited.add(resolved)
    text = index.read_text(encoding="utf-8")
    in_tree = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith(".. toctree::"):
            in_tree = True
            continue
        if not in_tree:
            continue
        if not line.strip():
            continue
        if line.startswith("   :"):
            continue
        if not line.startswith("   "):
            in_tree = False
            continue
        raw_target = line.strip().lstrip("/")
        child = (index.parent / raw_target).with_suffix(".rst")
        if not child.is_file():
            child = DOCS / f"{raw_target}.rst"
        if child.is_file():
            rel = str(child.relative_to(DOCS)).replace("\\", "/").removesuffix(".rst")
            docs.add(rel)
            _toctree_docs(child, docs, visited)
        else:
            docs.add(raw_target)
    return docs


def test_capabilities_check() -> None:
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_capabilities.py"), "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_capabilities_yaml_schema() -> None:
    catalog = yaml.safe_load(
        (DOCS / "catalog" / "capabilities.yaml").read_text(encoding="utf-8")
    )
    allowed = {"stable", "experimental", "adapter-only", "planned", "compatibility", "legacy"}
    for item in catalog["capabilities"]:
        assert item["status"] in allowed
        assert not str(item["function"]).startswith("uc.svi")


def test_roadmap_does_not_claim_core_objects_missing() -> None:
    forbidden_claims = (
        "There is no StudyArea",
        "None of Phases 1–4 are implemented",
        "existing-API closure",
    )
    hits: list[str] = []
    for rel in (
        "docs/source/index.rst",
        "docs/source/development/roadmap.rst",
        "README.md",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        for claim in forbidden_claims:
            if claim in text:
                hits.append(f"{rel}: {claim}")
    assert hits == []


def test_conf_does_not_write_capabilities() -> None:
    text = (DOCS / "conf.py").read_text(encoding="utf-8")
    assert "_write_capabilities_rst" not in text
    tree = ast.parse(text)
    assert tree is not None
