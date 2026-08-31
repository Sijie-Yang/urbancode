"""Filter Global Streetscapes metadata and build a TCIS download list.

Official order: filter the 10M tables, download only the kept rows at
1024 px, then run TCIS. Do not walk or copy NAS originals first.

    python examples/live/build_gs_catalog.py filter-metadata
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DEFAULT_ROOT = Path("/mnt/data/global-streetscapes")
DEFAULT_OUT = Path("/data/sijie/gs")

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
SKIP_DIR_NAMES = {"@eadir", ".ds_store", ".trash", "__macosx"}

# TCIS was trained on daytime street photos. Night lighting breaks
# vegetation/sky/shade cues. Other GS labels (front, quality, glare,
# pano_status) are diagnostics, not hard gates: the eight-city GSV
# run scored every file on disk.
FILTERS = {
    "lighting_condition": {"day", "daytime"},
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_skip_dir(name: str) -> bool:
    return name.lower() in SKIP_DIR_NAMES or name.startswith(".")


def _norm(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    return text.replace(" ", "_")


def _passes_filter(row: dict[str, str]) -> bool:
    for key, allowed in FILTERS.items():
        if key not in row:
            continue
        raw = row.get(key)
        if raw is None or raw == "":
            return False
        if _norm(raw) not in allowed:
            return False
    return True


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def walk_images(
    image_root: Path,
    out_dir: Path,
    countries_only: tuple[str, ...] | None = None,
) -> dict:
    """List on-disk images country by country. Resume-safe TSV."""
    dest = out_dir / "on_disk.tsv"
    progress_path = out_dir / "walk_progress.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    done_countries: set[str] = set()
    if progress_path.is_file():
        done_countries = set(json.loads(progress_path.read_text()).get("countries", []))

    new_file = not dest.is_file()
    n_written = 0
    if dest.is_file():
        with dest.open(encoding="utf-8") as handle:
            n_written = max(sum(1 for _ in handle) - 1, 0)

    wanted = {item.upper() for item in countries_only} if countries_only else None
    countries = sorted(
        path
        for path in image_root.iterdir()
        if path.is_dir()
        and not _is_skip_dir(path.name)
        and (wanted is None or path.name.upper() in wanted)
    )
    with dest.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        if new_file:
            writer.writerow(["uuid", "relative_path", "iso3", "city", "bytes"])
        for country in countries:
            if country.name in done_countries:
                print(f"skip {country.name} (already walked)", flush=True)
                continue
            city_n = file_n = 0
            for city in sorted(path for path in country.iterdir() if path.is_dir() and not _is_skip_dir(path.name)):
                city_n += 1
                for batch in sorted(path for path in city.iterdir() if path.is_dir() and not _is_skip_dir(path.name)):
                    with os.scandir(batch) as entries:
                        for entry in entries:
                            if not entry.is_file():
                                continue
                            suffix = Path(entry.name).suffix.lower()
                            if suffix not in IMAGE_SUFFIXES:
                                continue
                            try:
                                size = entry.stat().st_size
                            except OSError:
                                size = -1
                            rel = f"{country.name}/{city.name}/{batch.name}/{entry.name}"
                            writer.writerow([Path(entry.name).stem, rel, country.name, city.name, size])
                            file_n += 1
                    handle.flush()
            done_countries.add(country.name)
            n_written += file_n
            _write_json(
                progress_path,
                {
                    "countries": sorted(done_countries),
                    "n_files": n_written,
                    "last_country": country.name,
                    "last_country_files": file_n,
                    "last_country_cities": city_n,
                    "updated": _utc_now(),
                },
            )
            print(
                f"{_utc_now()} walked {country.name} cities={city_n} files={file_n} total={n_written}",
                flush=True,
            )

    inventory = {
        "image_root": str(image_root),
        "on_disk_tsv": str(dest),
        "n_files": n_written,
        "n_countries": len(done_countries),
        "countries": sorted(done_countries),
        "finished": _utc_now(),
    }
    _write_json(out_dir / "inventory.json", inventory)
    return inventory


def _read_matched_csv(path: Path, usecols: tuple[str, ...], wanted: set[str]) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    seen = 0
    matched = 0
    for chunk in pd.read_csv(path, usecols=lambda col: col in usecols, chunksize=250_000):
        seen += int(len(chunk))
        hit = chunk[chunk["uuid"].astype(str).isin(wanted)]
        if not hit.empty:
            parts.append(hit)
            matched += int(len(hit))
        print(f"  {path.name} {seen} matched={matched}", flush=True)
        if matched >= len(wanted):
            break
    if not parts:
        return pd.DataFrame(columns=list(usecols))
    return pd.concat(parts, ignore_index=True)


def _vector_filter(frame: pd.DataFrame) -> pd.Series:
    keep = pd.Series(True, index=frame.index)
    for key, allowed in FILTERS.items():
        if key not in frame.columns:
            continue
        values = frame[key].map(_norm)
        keep &= values.isin(allowed)
    return keep


def catalog_from_files(out_dir: Path) -> dict:
    """Build a TCIS catalog from on-disk files without waiting on metadata."""
    disk_path = out_dir / "on_disk.tsv"
    if not disk_path.is_file():
        raise FileNotFoundError(f"run walk first: missing {disk_path}")
    disk = pd.read_csv(disk_path, sep="\t")
    catalog = pd.DataFrame(
        {
            "image_id": disk["uuid"].astype(str),
            "relative_path": disk["relative_path"].astype(str),
            "longitude": None,
            "latitude": None,
            "heading": None,
            "fov": None,
            "pitch": None,
            "captured_at": None,
            "panorama_id": None,
            "provider": "global-streetscapes",
            "license": None,
            "city_id": disk["city"].astype(str),
            "country": None,
            "iso3": disk["iso3"].astype(str),
            "view_type": "streetview",
            "parse_error": "metadata_not_joined",
        }
    )
    dest = out_dir / "catalog_files.parquet"
    catalog.to_parquet(dest, index=False)
    summary = {
        "finished": _utc_now(),
        "n_images": int(len(catalog)),
        "catalog": str(dest),
        "note": "paths only; lon/lat joined later by the catalog command",
    }
    _write_json(out_dir / "catalog_files_summary.json", summary)
    return summary


def join_and_filter(gs_root: Path, out_dir: Path) -> dict:
    """Join on-disk files with official tables and apply TCIS filters."""
    disk_path = out_dir / "on_disk.tsv"
    if not disk_path.is_file():
        raise FileNotFoundError(f"run walk first: missing {disk_path}")

    disk = pd.read_csv(disk_path, sep="\t")
    if disk.empty:
        raise FileNotFoundError(f"on_disk.tsv is empty: {disk_path}")
    disk["uuid"] = disk["uuid"].astype(str)
    wanted = set(disk["uuid"])
    print(f"on_disk={len(disk)} unique_uuid={len(wanted)}", flush=True)

    meta_keep = (
        "uuid",
        "source",
        "orig_id",
        "lat",
        "lon",
        "datetime_local",
        "heading",
        "projection_type",
        "hFoV",
        "vFoV",
        "width",
        "height",
    )
    ctx_keep = (
        "uuid",
        "platform",
        "weather",
        "view_direction",
        "lighting_condition",
        "glare",
        "quality",
        "reflection",
        "pano_status",
    )
    city_keep = ("uuid", "city", "city_ascii", "country", "iso3", "continent")

    uniques: dict[str, Counter[str]] = defaultdict(Counter)

    meta_csv = gs_root / "data" / "metadata_common_attributes.csv"
    print(f"streaming {meta_csv}", flush=True)
    meta = _read_matched_csv(meta_csv, meta_keep, wanted)

    ctx_csv = gs_root / "data" / "contextual.csv"
    print(f"streaming {ctx_csv}", flush=True)
    ctx = _read_matched_csv(ctx_csv, ctx_keep, wanted)
    for key in ctx_keep[1:]:
        if key in ctx.columns:
            for value, count in ctx[key].map(_norm).replace("", "<empty>").value_counts().items():
                uniques[key][str(value)] += int(count)

    city_csv = gs_root / "data" / "simplemaps.csv"
    print(f"streaming {city_csv}", flush=True)
    cities = _read_matched_csv(city_csv, city_keep, wanted)

    frame = disk.merge(meta, on="uuid", how="left")
    if not ctx.empty:
        frame = frame.merge(ctx, on="uuid", how="left")
    if not cities.empty:
        frame = frame.merge(cities, on="uuid", how="left", suffixes=("", "_meta"))

    filtered = frame.loc[_vector_filter(frame)].copy()

    catalog = pd.DataFrame(
        {
            "image_id": filtered["uuid"].astype(str),
            "relative_path": filtered["relative_path"].astype(str),
            "longitude": pd.to_numeric(filtered.get("lon"), errors="coerce"),
            "latitude": pd.to_numeric(filtered.get("lat"), errors="coerce"),
            "heading": pd.to_numeric(filtered.get("heading"), errors="coerce"),
            "fov": pd.to_numeric(filtered.get("hFoV"), errors="coerce"),
            "pitch": None,
            "captured_at": filtered.get("datetime_local"),
            "panorama_id": filtered.get("orig_id"),
            "provider": filtered.get("source"),
            "license": None,
            "city_id": filtered.get("city_ascii", filtered.get("city")),
            "country": filtered.get("country"),
            "iso3": filtered.get("iso3", filtered.get("iso3_meta")),
            "view_type": "streetview",
            "parse_error": None,
        }
    )
    if catalog["image_id"].duplicated().any():
        catalog = catalog.drop_duplicates(subset=["image_id"], keep="first")

    on_disk_out = out_dir / "on_disk.parquet"
    filtered_out = out_dir / "catalog_filtered.parquet"
    all_joined = out_dir / "on_disk_joined.parquet"
    frame.to_parquet(all_joined, index=False)
    disk.to_parquet(on_disk_out, index=False)
    catalog.to_parquet(filtered_out, index=False)

    cities688 = pd.read_csv(gs_root / "cities688.csv")
    summary = {
        "finished": _utc_now(),
        "declared_cities": int(len(cities688)),
        "declared_images": int(pd.to_numeric(cities688["img_count"], errors="coerce").fillna(0).sum()),
        "on_disk_images": int(len(disk)),
        "on_disk_countries": int(disk["iso3"].nunique()),
        "on_disk_cities": int(disk["city"].nunique()),
        "joined_with_metadata": int(frame["lat"].notna().sum()) if "lat" in frame.columns else 0,
        "filtered_images": int(len(catalog)),
        "filtered_cities": int(catalog["city_id"].nunique()) if "city_id" in catalog.columns else 0,
        "metadata_rows_matched": int(len(meta)),
        "contextual_rows_matched": int(len(ctx)),
        "simplemaps_rows_matched": int(len(cities)),
        "has_sgp_images": bool((disk["iso3"] == "SGP").any()),
        "filter": {key: sorted(values) for key, values in FILTERS.items()},
        "contextual_uniques": {key: dict(counter.most_common()) for key, counter in uniques.items()},
        "on_disk_by_country": disk.groupby("iso3").size().sort_values(ascending=False).to_dict(),
        "catalog": str(filtered_out),
    }
    _write_json(out_dir / "catalog_summary.json", summary)
    print(json.dumps({k: summary[k] for k in ("on_disk_images", "filtered_images", "has_sgp_images")}, indent=2))
    return summary


def filter_metadata(gs_root: Path, out_dir: Path) -> dict:
    """Filter the official 10M tables. No images required."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ctx_keep = (
        "uuid",
        "source",
        "orig_id",
        "platform",
        "weather",
        "view_direction",
        "lighting_condition",
        "glare",
        "quality",
        "reflection",
        "pano_status",
    )
    meta_keep = (
        "uuid",
        "lat",
        "lon",
        "datetime_local",
        "heading",
        "projection_type",
        "hFoV",
        "vFoV",
        "width",
        "height",
    )
    city_keep = ("uuid", "city", "city_ascii", "country", "iso3", "continent")
    uniques: dict[str, Counter[str]] = defaultdict(Counter)

    ctx_csv = gs_root / "data" / "contextual.csv"
    print(f"filtering {ctx_csv}", flush=True)
    ctx_parts: list[pd.DataFrame] = []
    seen = 0
    for chunk in pd.read_csv(ctx_csv, usecols=lambda col: col in ctx_keep, chunksize=250_000):
        seen += int(len(chunk))
        for key in ("view_direction", "lighting_condition", "glare", "quality", "reflection", "pano_status"):
            if key in chunk.columns:
                for value, count in chunk[key].map(_norm).fillna("<empty>").replace("", "<empty>").value_counts().items():
                    uniques[key][str(value)] += int(count)
        keep = _vector_filter(chunk)
        hit = chunk.loc[keep]
        if not hit.empty:
            ctx_parts.append(hit)
        print(f"  contextual {seen} kept={sum(len(p) for p in ctx_parts)}", flush=True)
    if not ctx_parts:
        raise FileNotFoundError("no rows passed the contextual TCIS filters")
    ctx = pd.concat(ctx_parts, ignore_index=True)
    wanted = set(ctx["uuid"].astype(str))
    print(f"contextual kept={len(ctx)} unique={len(wanted)}", flush=True)

    print("joining metadata_common_attributes", flush=True)
    meta = _read_matched_csv(gs_root / "data" / "metadata_common_attributes.csv", meta_keep, wanted)
    print(f"metadata matched={len(meta)}", flush=True)

    print("joining simplemaps", flush=True)
    cities = _read_matched_csv(gs_root / "data" / "simplemaps.csv", city_keep, wanted)

    frame = ctx.merge(meta, on="uuid", how="inner")
    if not cities.empty:
        frame = frame.merge(cities, on="uuid", how="left")

    catalog = pd.DataFrame(
        {
            "image_id": frame["uuid"].astype(str),
            "uuid": frame["uuid"].astype(str),
            "source": frame["source"],
            "orig_id": frame["orig_id"],
            "relative_path": frame["uuid"].astype(str) + ".jpeg",
            "longitude": pd.to_numeric(frame.get("lon"), errors="coerce"),
            "latitude": pd.to_numeric(frame.get("lat"), errors="coerce"),
            "heading": pd.to_numeric(frame.get("heading"), errors="coerce"),
            "fov": pd.to_numeric(frame.get("hFoV"), errors="coerce"),
            "pitch": None,
            "captured_at": frame.get("datetime_local"),
            "panorama_id": frame.get("orig_id"),
            "provider": frame["source"],
            "license": None,
            "city_id": frame.get("city_ascii", frame.get("city")),
            "country": frame.get("country"),
            "iso3": frame.get("iso3"),
            "view_type": "streetview",
            "parse_error": None,
        }
    )
    catalog = catalog.drop_duplicates(subset=["image_id"], keep="first")
    dest = out_dir / "catalog_filtered.parquet"
    csv_dest = out_dir / "catalog_download.csv"
    catalog.to_parquet(dest, index=False)
    catalog[["uuid", "source", "orig_id"]].to_csv(csv_dest, index=False)

    by_source = catalog["source"].astype(str).value_counts().to_dict()
    by_country = (
        catalog["iso3"].astype(str).value_counts().head(20).to_dict()
        if "iso3" in catalog.columns
        else {}
    )
    diagnostics = {}
    for key in ("projection_type", "pano_status", "view_direction", "quality"):
        src = frame if key in frame.columns else None
        if src is not None:
            diagnostics[key] = src[key].map(_norm).fillna("<empty>").value_counts().to_dict()
    summary = {
        "finished": _utc_now(),
        "declared_images": 10_004_551,
        "filtered_images": int(len(catalog)),
        "filtered_cities": int(catalog["city_id"].nunique()) if "city_id" in catalog.columns else 0,
        "by_source": by_source,
        "by_iso3_top20": by_country,
        "daytime_mix": diagnostics,
        "has_singapore": bool((catalog.get("iso3") == "SGP").any()) if "iso3" in catalog.columns else False,
        "filter": {key: sorted(values) for key, values in FILTERS.items()},
        "contextual_uniques": {key: dict(counter.most_common()) for key, counter in uniques.items()},
        "download_size": "mapillary thumb_1024 + kartaview fileurlProc, then resize 1024x512",
        "catalog": str(dest),
        "download_csv": str(csv_dest),
        "note": "Hard filter is daytime only. Other labels are reported, not dropped.",
    }
    _write_json(out_dir / "filter_summary.json", summary)
    print(json.dumps({k: summary[k] for k in ("filtered_images", "by_source", "has_singapore")}, indent=2, default=str))
    return summary


def copy_smoke(out_dir: Path, dest_root: Path, n: int) -> dict:
    """Copy the first N filtered images off NAS for the TCIS gate."""
    catalog_path = out_dir / "catalog_filtered.parquet"
    if not catalog_path.is_file():
        catalog_path = out_dir / "catalog_files.parquet"
    if not catalog_path.is_file():
        raise FileNotFoundError("run catalog or catalog-files first")
    catalog = pd.read_parquet(catalog_path)
    if catalog.empty:
        raise FileNotFoundError("filtered catalog is empty")
    sample = catalog.head(n).copy()
    src_root = Path(json.loads((out_dir / "inventory.json").read_text())["image_root"])
    dest_root.mkdir(parents=True, exist_ok=True)
    copied = 0
    missing = 0
    for rel in sample["relative_path"]:
        src = src_root / rel
        dest = dest_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not src.is_file():
            missing += 1
            continue
        if dest.is_file() and dest.stat().st_size > 0:
            copied += 1
            continue
        shutil.copy2(src, dest)
        copied += 1
    smoke_catalog = dest_root.parent / "catalog_smoke.parquet"
    sample.to_parquet(smoke_catalog, index=False)
    payload = {
        "n_requested": n,
        "n_copied": copied,
        "n_missing": missing,
        "image_root": str(dest_root),
        "catalog": str(smoke_catalog),
        "finished": _utc_now(),
    }
    _write_json(dest_root.parent / "smoke_copy.json", payload)
    return payload


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("walk", "catalog", "catalog-files", "filter-metadata", "copy-smoke", "all"),
    )
    parser.add_argument("--gs-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument(
        "--countries",
        default="",
        help="Optional comma-separated ISO3 codes to walk (e.g. ARE,AUS).",
    )
    args = parser.parse_args(argv)
    images = args.gs_root / "images"
    countries = tuple(item.strip() for item in args.countries.split(",") if item.strip())
    if args.command in {"walk", "all"}:
        result = walk_images(images, args.out, countries or None)
        if args.command == "walk":
            return result
    if args.command == "catalog-files":
        return catalog_from_files(args.out)
    if args.command == "filter-metadata":
        return filter_metadata(args.gs_root, args.out)
    if args.command in {"catalog", "all"}:
        result = join_and_filter(args.gs_root, args.out)
        if args.command == "catalog":
            return result
    return copy_smoke(args.out, args.out / "smoke" / "images", args.n)


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, default=str))
