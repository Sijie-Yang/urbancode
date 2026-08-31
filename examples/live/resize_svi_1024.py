"""Resize street-view JPEGs to the 92k Singapore size: 1024x512."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from PIL import Image

TARGET = (1024, 512)


def _resize_one(path_str: str, quality: int) -> str:
    path = Path(path_str)
    try:
        with Image.open(path) as image:
            image = image.convert("RGB")
            if image.size == TARGET:
                return "skip"
            image = image.resize(TARGET, Image.Resampling.LANCZOS)
            tmp = path.with_suffix(path.suffix + ".tmp.jpg")
            image.save(tmp, format="JPEG", quality=quality, optimize=True)
        tmp.replace(path)
        return "ok"
    except Exception as exc:
        return f"err:{exc}"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", type=Path)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--quality", type=int, default=85)
    args = parser.parse_args(argv)
    files: list[str] = []
    for root in args.roots:
        files.extend(str(p) for p in sorted(root.glob("*.jpg")))
        files.extend(str(p) for p in sorted(root.glob("*.jpeg")))
    print(f"files={len(files)} target={TARGET[0]}x{TARGET[1]} workers={args.workers}", flush=True)
    ok = skip = err = 0
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(_resize_one, path, args.quality) for path in files]
        for i, fut in enumerate(as_completed(futures), 1):
            result = fut.result()
            if result == "ok":
                ok += 1
            elif result == "skip":
                skip += 1
            else:
                err += 1
                print(result, flush=True)
            if i % 5000 == 0 or i == len(futures):
                print(f"progress {i}/{len(files)} ok={ok} skip={skip} err={err}", flush=True)
    print(f"done ok={ok} skip={skip} err={err}", flush=True)
    Path("/data/sijie/tcis_runs/resize.done").write_text(
        f"ok={ok} skip={skip} err={err}\n", encoding="utf-8"
    )
    if err:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
