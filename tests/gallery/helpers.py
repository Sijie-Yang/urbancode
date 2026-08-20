from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "examples" / "data" / "punggol_pocket"
GALLERY_STATIC = REPO / "docs" / "source" / "_static" / "gallery"
BBOX = (103.905, 1.400, 103.915, 1.410)
TITLE = "Punggol, Singapore"


def load_offline(filename: str):
    path = REPO / "examples" / "offline" / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
