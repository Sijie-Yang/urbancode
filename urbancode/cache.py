"""Unified on-disk cache. Never write downloads into the package tree."""

from __future__ import annotations

import os
from pathlib import Path

_CACHE_SUBDIRS = ("models", "network", "imagery", "downloads")


def cache_root() -> Path:
    """Return the UrbanCode cache root.

    Honors ``URBANCODE_CACHE_DIR`` when set; otherwise uses
    ``platformdirs.user_cache_dir("urbancode")``.
    """
    override = os.environ.get("URBANCODE_CACHE_DIR")
    if override:
        root = Path(override).expanduser().resolve()
    else:
        from platformdirs import user_cache_dir

        root = Path(user_cache_dir("urbancode"))
    root.mkdir(parents=True, exist_ok=True)
    for name in _CACHE_SUBDIRS:
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def models_dir() -> Path:
    """Cached model weights and feature stats."""
    path = cache_root() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def network_dir() -> Path:
    """Cached OSM / network downloads."""
    path = cache_root() / "network"
    path.mkdir(parents=True, exist_ok=True)
    return path


def imagery_dir() -> Path:
    """Cached rasters."""
    path = cache_root() / "imagery"
    path.mkdir(parents=True, exist_ok=True)
    return path


def downloads_dir() -> Path:
    """Generic download / Hugging Face cache."""
    path = cache_root() / "downloads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def huggingface_dir() -> Path:
    """Hugging Face hub cache inside the UrbanCode cache tree."""
    path = downloads_dir() / "huggingface"
    path.mkdir(parents=True, exist_ok=True)
    return path
