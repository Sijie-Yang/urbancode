#!/usr/bin/env python3
"""Validate real and contract dataset manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_lib import CONTRACTS, REAL_DATA, REAL_MANIFEST_FIELDS  # noqa: E402

REQUIRED_FILES = ("manifest.json", "LICENSE.md", "README.md", "checksums.sha256")
SKIP_CHECKSUM = {"checksums.sha256"}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_nan)


def _reject_nan(value: str):
    raise ValueError(f"non-standard JSON constant {value!r}")


def iter_dataset_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    found: list[Path] = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and not child.name.startswith(("_", ".")):
            if (child / "manifest.json").exists():
                found.append(child)
    return found


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def listed_files(dataset: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(dataset.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(dataset).as_posix()
        if path.name.startswith(".") or rel in SKIP_CHECKSUM:
            continue
        files.append(path)
    return files


def _parse_sha_file(path: Path) -> dict[str, str]:
    listed: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split(maxsplit=1)
        listed[rel.strip()] = digest
    return listed


def validate_real(path: Path) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        if not (path / name).is_file():
            errors.append(f"{path.name}: missing {name}")
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        return errors
    try:
        data = _load(manifest_path)
    except ValueError as exc:
        return [f"{path.name}: {exc}"]
    if data.get("synthetic") is True:
        errors.append(f"{path.name}: real dataset must not set synthetic: true")
    record_path = path / "dataset.json"
    try:
        record = _load(record_path) if record_path.is_file() else data
    except ValueError as exc:
        errors.append(f"{path.name}: dataset.json {exc}")
        record = {}
    for key in REAL_MANIFEST_FIELDS:
        if key not in record:
            errors.append(f"{path.name}: missing {key}")
    checksums = dict(record.get("file_checksums") or {})
    sha_file = path / "checksums.sha256"
    listed = _parse_sha_file(sha_file) if sha_file.is_file() else {}
    if not checksums and not listed:
        errors.append(f"{path.name}: empty file_checksums")
    for rel, digest in listed.items():
        target = path / rel
        if not target.is_file():
            errors.append(f"{path.name}: checksum path missing {rel}")
            continue
        actual = sha256(target)
        if actual != digest:
            errors.append(f"{path.name}: SHA-256 mismatch {rel}")
        if checksums and rel in checksums and checksums[rel] != actual:
            errors.append(f"{path.name}: file_checksums mismatch {rel}")
    for record in data.get("layers") or []:
        if record.get("kind") != "raster":
            continue
        if not record.get("crs"):
            errors.append(f"{path.name}: raster {record.get('name')} missing CRS")
    return errors


def validate_contract(path: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        return [f"{path.name}: missing manifest.json"]
    try:
        data = _load(manifest_path)
    except ValueError as exc:
        return [f"{path.name}: {exc}"]
    if data.get("synthetic") is not True:
        errors.append(f"{path.name}: contract fixture must set synthetic: true")
    return errors


def write_checksums(dataset: Path, files: list[Path] | None = None) -> None:
    del files
    for name in ("dataset.json", "manifest.json"):
        manifest_path = dataset / name
        if not manifest_path.is_file():
            continue
        text = manifest_path.read_text(encoding="utf-8").replace(": NaN", ": null")
        data = json.loads(text)
        if name == "manifest.json":
            metric = (data.get("study_area") or {}).get("metric_crs") or "EPSG:32648"
            for record in data.get("layers") or []:
                if record.get("kind") == "raster" and not record.get("crs"):
                    record["crs"] = metric
                nodata = record.get("nodata")
                if isinstance(nodata, float) and math.isnan(nodata):
                    record["nodata"] = None
        manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    payload = [
        path
        for path in listed_files(dataset)
        if path.name not in {"dataset.json", "manifest.json", "checksums.sha256"}
    ]
    payload_checksums = {
        path.relative_to(dataset).as_posix(): sha256(path) for path in payload
    }
    dataset_path = dataset / "dataset.json"
    if dataset_path.is_file():
        data = json.loads(dataset_path.read_text(encoding="utf-8"))
        data["file_checksums"] = payload_checksums
        dataset_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    elif (dataset / "manifest.json").is_file():
        data = json.loads((dataset / "manifest.json").read_text(encoding="utf-8"))
        if "file_checksums" in data:
            data["file_checksums"] = payload_checksums
            (dataset / "manifest.json").write_text(
                json.dumps(data, indent=2) + "\n", encoding="utf-8"
            )
    lines = []
    for path in listed_files(dataset):
        rel = path.relative_to(dataset).as_posix()
        lines.append(f"{sha256(path)}  {rel}")
    (dataset / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        if REAL_DATA.is_dir():
            for path in iter_dataset_dirs(REAL_DATA):
                write_checksums(path)
        if CONTRACTS.is_dir():
            for path in iter_dataset_dirs(CONTRACTS):
                for manifest in path.glob("manifest.json"):
                    text = manifest.read_text(encoding="utf-8").replace(": NaN", ": null")
                    manifest.write_text(
                        json.dumps(json.loads(text), indent=2) + "\n", encoding="utf-8"
                    )
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
    if args.check or args.write:
        print("dataset manifests ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
