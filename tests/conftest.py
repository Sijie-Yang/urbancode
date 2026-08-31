"""Shared pytest fixtures. Unit tests must stay offline."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "urbancode-mpl")
)


@pytest.fixture
def cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "uc-cache"
    monkeypatch.setenv("URBANCODE_CACHE_DIR", str(root))
    return root


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    if os.environ.get("UC_FAIL_ON_SKIP") != "1":
        return
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    skipped = reporter.stats.get("skipped", []) if reporter else []
    if skipped:
        session.exitstatus = 1
        print(f"\nUC_FAIL_ON_SKIP: {len(skipped)} tests skipped")
