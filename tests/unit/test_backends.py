from __future__ import annotations

import pytest

import urbancode as uc
from urbancode.errors import MissingExtraError


def test_backends_available_does_not_import_torch() -> None:
    import sys

    had = "torch" in sys.modules
    found = uc.backends.available()
    assert "osmnx" in found
    assert "geopandas" in found
    if not had:
        assert "torch" not in sys.modules


def test_backends_info_and_unknown() -> None:
    info = uc.backends.info("geopandas")
    assert info["extra"] == "vector"
    assert "urbancode[vector]" in info["install"]
    with pytest.raises(KeyError, match="unknown backend"):
        uc.backends.info("not_a_backend")


def test_backends_status_and_explain() -> None:
    all_status = uc.backends.status()
    assert "geopandas" in all_status
    detail = uc.backends.explain("geopandas")
    assert "version" in detail
    assert detail["extra"] == "vector"


def test_backend_extras_match_pyproject() -> None:
    from pathlib import Path

    from urbancode.backends import _BACKENDS

    text = Path("pyproject.toml").read_text(encoding="utf-8")
    for _name, (_module, extra) in _BACKENDS.items():
        assert f"{extra} =" in text or f"{extra}=" in text, extra


def test_backends_require_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(module, extra):
        raise MissingExtraError(
            f'{module} is required. Install with: pip install "urbancode[{extra}]"'
        )

    monkeypatch.setattr("urbancode.backends.require_extra", boom)
    with pytest.raises(MissingExtraError, match="urbancode\\[svi\\]"):
        uc.backends.require("torch")
