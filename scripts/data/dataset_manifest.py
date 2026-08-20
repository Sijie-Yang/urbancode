#!/usr/bin/env python3
"""Validate real and contract dataset manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_lib import CONTRACTS, REAL_DATA, REAL_MANIFEST_FIELDS  # noqa: E402

REQUIRED_FILES = ("manifest.json", "LICENSE.md", "README.md", "checksums.sha256")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_dataset_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    found: list[Path] = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and not child.name.startswith(("_", ".")):
            if (child / "manifest.json").exists():
                found.append(child)
    return found


def validate_real(path: Path) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        if not (path / name).is_file():
            errors.append(f"{path.name}: missing {name}")
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        return errors
    data = _load(manifest_path)
    if data.get("synthetic") is True:
        errors.append(f"{path.name}: real dataset must not set synthetic: true")
    for key in REAL_MANIFEST_FIELDS:
        if key not in data:
            errors.append(f"{path.name}: missing {key}")
    checksums = data.get("file_checksums") or {}
    sha_file = path / "checksums.sha256"
    if sha_file.is_file() and checksums:
        listed = {
            line.split(maxsplit=1)[1].strip()
            for line in sha_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
        for rel in checksums:
            if rel not in listed and not (path / rel).is_file():
                errors.append(f"{path.name}: checksum path missing {rel}")
    return errors


def validate_contract(path: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        return [f"{path.name}: missing manifest.json"]
    data = _load(manifest_path)
    if data.get("synthetic") is not True:
        errors.append(f"{path.name}: contract fixture must set synthetic: true")
    return errors


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksums(dataset: Path, files: list[Path]) -> None:
    lines = []
    checksums = {}
    for path in files:
        rel = path.relative_to(dataset).as_posix()
        digest = sha256(path)
        checksums[rel] = digest
        lines.append(f"{digest}  {rel}")
    (dataset / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest_path = dataset / "manifest.json"
    data = _load(manifest_path)
    data["file_checksums"] = checksums
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []
    if REAL_DATA.is_dir():
        for path in iter_dataset_dirs(REAL_DATA):
            errors.extend(validate_real(path))
    if CONTRACTS.is_dir():
        for path in iter_dataset_dirs(CONTRACTS):
            errors.extend(validate_contract(path))
    if errors:
        print("\n".join(errors))
        return 1
    if args.check:
        print("dataset manifests ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
