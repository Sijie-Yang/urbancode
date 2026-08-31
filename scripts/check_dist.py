#!/usr/bin/env python3
"""Verify sdist/wheel size, contents, and package metadata."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from pathlib import Path

MAX_MB = 5
WEIGHT_SUFFIXES = (".pth", ".pth.tar")
FORBIDDEN_NAMES = (".DS_Store",)


def _assert_no_junk(names: list[str], label: str) -> None:
    weights = [n for n in names if n.endswith(WEIGHT_SUFFIXES)]
    junk = [n for n in names if Path(n).name in FORBIDDEN_NAMES]
    if weights:
        raise SystemExit(f"{label} contains weight files: {weights[:5]}")
    if junk:
        raise SystemExit(f"{label} contains system files: {junk[:5]}")


def check_wheel(path: Path) -> dict[str, object]:
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb >= MAX_MB:
        raise SystemExit(f"{path.name} is {size_mb:.1f} MB (limit {MAX_MB})")
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        metadata = zf.read(next(n for n in names if n.endswith("METADATA"))).decode(
            "utf-8"
        )
    _assert_no_junk(names, path.name)
    if "Name: urbancode" not in metadata:
        raise SystemExit(f"{path.name} metadata is missing Name: urbancode")
    if "Requires-Python" not in metadata:
        raise SystemExit(f"{path.name} metadata is missing Requires-Python")
    return {"path": path.name, "size_mb": round(size_mb, 2), "files": len(names)}


def check_sdist(path: Path) -> dict[str, object]:
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb >= MAX_MB:
        raise SystemExit(f"{path.name} is {size_mb:.1f} MB (limit {MAX_MB})")
    with tarfile.open(path, "r:gz") as tf:
        names = [m.name for m in tf.getmembers() if m.isfile()]
        pkg = next(n for n in names if n.endswith("PKG-INFO"))
        metadata = tf.extractfile(pkg).read().decode("utf-8")  # type: ignore[union-attr]
    _assert_no_junk(names, path.name)
    if "Name: urbancode" not in metadata:
        raise SystemExit(f"{path.name} PKG-INFO is missing Name: urbancode")
    return {"path": path.name, "size_mb": round(size_mb, 2), "files": len(names)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dist", nargs="?", default="dist", type=Path)
    args = parser.parse_args()
    dist = args.dist
    wheels = sorted(dist.glob("*.whl"))
    sdists = sorted(dist.glob("*.tar.gz"))
    if not wheels:
        raise SystemExit(f"no wheel in {dist}")
    if not sdists:
        raise SystemExit(f"no sdist in {dist}")
    for wheel in wheels:
        info = check_wheel(wheel)
        print(f"wheel {info['path']} {info['size_mb']} MB, {info['files']} files")
    for sdist in sdists:
        info = check_sdist(sdist)
        print(f"sdist {info['path']} {info['size_mb']} MB, {info['files']} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
