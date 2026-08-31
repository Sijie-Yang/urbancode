"""Shared PNG checks. Not a pixel-golden comparison."""

from __future__ import annotations

from pathlib import Path


def assert_gallery_png(path: Path) -> None:
    from PIL import Image
    import numpy as np

    assert path.is_file(), f"missing figure {path}"
    image = Image.open(path).convert("RGB")
    assert image.width >= 600, f"width {image.width} < 600"
    assert image.height >= 400, f"height {image.height} < 400"
    pixels = np.asarray(image, dtype=np.float32)
    assert float(pixels.std()) > 5.0, f"std {pixels.std()} <= 5"
    unique = np.unique(pixels.reshape(-1, 3), axis=0)
    assert unique.shape[0] > 32, f"only {unique.shape[0]} unique RGB colours"
