"""Download Places365 ResNet weights into the user cache, never the package."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from pathlib import Path

from urbancode.cache import models_dir
from urbancode.streetview.contract import ContractError

_DATA_DIR = Path(__file__).resolve().parent / "data"
MANIFEST_PATH = _DATA_DIR / "places365_manifest.json"
BUNDLED_LABELS = _DATA_DIR / "categories_places365.txt"


def load_places365_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_places365_weights(*, refresh: bool = False) -> Path:
    """Return the cached Places365 checkpoint. Requires the ``svi`` extra to use."""
    manifest = load_places365_manifest()
    dest = models_dir() / manifest["filename"]
    expected = manifest.get("sha256")
    if dest.exists() and not refresh:
        if not expected or _sha256(dest) == expected:
            return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    urllib.request.urlretrieve(manifest["url"], tmp)
    if expected:
        actual = _sha256(tmp)
        if actual != expected:
            tmp.unlink(missing_ok=True)
            raise ContractError(
                f"SHA-256 mismatch for {dest.name}: got {actual}, expected {expected}"
            )
    os.replace(tmp, dest)
    return dest


def places365_labels() -> Path:
    manifest = load_places365_manifest()
    expected = manifest.get("labels_sha256")
    if BUNDLED_LABELS.exists():
        if expected and _sha256(BUNDLED_LABELS) != expected:
            raise ContractError(
                f"SHA-256 mismatch for bundled Places365 labels: "
                f"got {_sha256(BUNDLED_LABELS)}, expected {expected}"
            )
        return BUNDLED_LABELS
    dest = models_dir() / "categories_places365.txt"
    if dest.exists():
        if expected and _sha256(dest) != expected:
            dest.unlink()
        else:
            return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/csailvision/places365/master/categories_places365.txt",
        dest,
    )
    actual = _sha256(dest)
    if expected and actual != expected:
        dest.unlink(missing_ok=True)
        raise ContractError(
            f"SHA-256 mismatch for downloaded Places365 labels: "
            f"got {actual}, expected {expected}"
        )
    return dest
