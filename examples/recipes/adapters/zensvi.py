"""Interop: uc.adapters.zensvi is the upstream zensvi module when installed."""

from __future__ import annotations

from pathlib import Path


def main(out_dir: str | Path) -> dict:
    import urbancode as uc
    from urbancode.errors import MissingExtraError

    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    note = dest / "zensvi_interop.txt"
    try:
        zensvi = uc.adapters.zensvi
        text = f"uc.adapters.zensvi is {zensvi.__name__}\n"
        name = zensvi.__name__
    except MissingExtraError as exc:
        text = f"zensvi extra missing: {exc}\n"
        name = None
    note.write_text(text, encoding="utf-8")
    return {
        "result": name,
        "figures": [],
        "artifacts": [note],
        "summary": text.strip(),
    }


if __name__ == "__main__":
    print(main(Path(__file__).resolve().parents[3] / "output" / "recipes" / "adapters" / "zensvi"))
