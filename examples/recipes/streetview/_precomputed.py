"""Load or create precomputed street-view ML artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from examples.recipes._common import REAL, streetview_dir

PRE = REAL / "streetview" / "precomputed"


def photo_path() -> Path:
    folder = streetview_dir()
    photos = sorted(folder.glob("*.jpg"))
    if not photos:
        raise FileNotFoundError(folder)
    return photos[0]


def load_or_run(name: str, runner):
    dest = PRE / f"{name}.json"
    if dest.is_file():
        return json.loads(dest.read_text(encoding="utf-8"))
    PRE.mkdir(parents=True, exist_ok=True)
    payload = runner(photo_path())
    dest.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    return payload
