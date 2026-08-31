from __future__ import annotations

from pathlib import Path


def test_package_data_excludes_weight_archives() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    start = text.index("[tool.setuptools.package-data]")
    end = text.index("[tool.setuptools.exclude-package-data]")
    include = text[start:end]
    assert "streetview/data/tcis_manifest.json" in include
    assert "streetview/data/feature_stats.npz" in include
    assert '"streetview/data/*"' not in include
    assert "resnet50_places365.pth.tar" not in include
    assert "*.pth.tar" in text[end:]


def test_places365_manifest_has_sha() -> None:
    from urbancode.streetview.places365 import load_places365_manifest

    manifest = load_places365_manifest()
    assert len(manifest["sha256"]) == 64
    assert manifest["filename"].endswith(".pth.tar")
