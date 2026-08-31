from __future__ import annotations

import importlib
import sys

import pytest

import urbancode as uc
from urbancode.errors import MissingExtraError


def test_adapters_namespace_is_lazy() -> None:
    assert "adapters" in uc.__all__
    had_zensvi = "zensvi" in sys.modules
    adapters = uc.adapters
    assert adapters.__name__ == "urbancode.adapters"
    if not had_zensvi:
        assert "zensvi" not in sys.modules


def test_unknown_adapter() -> None:
    with pytest.raises(AttributeError, match="no attribute"):
        _ = uc.adapters.not_a_real_backend


@pytest.mark.parametrize(
    ("name", "module", "extra"),
    [
        ("osmnx", "osmnx", "network"),
        ("zensvi", "zensvi", "download"),
        ("streetlevel", "streetlevel", "download"),
        ("city2graph", "city2graph", "graph"),
        ("pythermalcomfort", "pythermalcomfort", "climate"),
        ("geopandas", "geopandas", "vector"),
        ("shapely", "shapely", "vector"),
        ("momepy", "momepy", "network"),
        ("networkx", "networkx", "network"),
    ],
)
def test_adapter_import_or_hint(name: str, module: str, extra: str) -> None:
    try:
        imported = importlib.import_module(module)
    except ImportError:
        with pytest.raises(MissingExtraError, match=rf'urbancode\[{extra}\]'):
            getattr(uc.adapters, name)
        return
    assert getattr(uc.adapters, name).__name__ == imported.__name__
