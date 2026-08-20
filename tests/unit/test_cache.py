from __future__ import annotations

from pathlib import Path

from urbancode.cache import (
    cache_root,
    downloads_dir,
    huggingface_dir,
    imagery_dir,
    models_dir,
    network_dir,
)


def test_cache_root_honors_env(cache_dir: Path) -> None:
    root = cache_root()
    assert root == cache_dir.resolve()
    assert (root / "models").is_dir()
    assert (root / "network").is_dir()
    assert (root / "imagery").is_dir()
    assert (root / "downloads").is_dir()


def test_cache_subdirs(cache_dir: Path) -> None:
    assert models_dir() == cache_dir.resolve() / "models"
    assert network_dir() == cache_dir.resolve() / "network"
    assert imagery_dir() == cache_dir.resolve() / "imagery"
    assert downloads_dir() == cache_dir.resolve() / "downloads"
    assert huggingface_dir() == cache_dir.resolve() / "downloads" / "huggingface"


def test_import_urbancode_is_light() -> None:
    import sys

    heavy = {"torch", "osmnx", "rasterio", "geopandas", "matplotlib"}
    loaded = heavy.intersection(sys.modules)
    # A pre-existing environment may already have them imported; the package
    # itself must not import them during ``import urbancode``.
    before = set(sys.modules)
    import urbancode

    assert urbancode.__version__ == "0.3.0"
    added = set(sys.modules) - before
    assert not heavy.intersection(added), added
    del loaded
