"""Interop: uc.adapters.osmnx is the upstream osmnx module."""

from __future__ import annotations

from pathlib import Path


def main(out_dir: str | Path) -> dict:
    import urbancode as uc

    ox = uc.adapters.osmnx
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    note = dest / "osmnx_interop.txt"
    note.write_text(
        f"uc.adapters.osmnx is {ox.__name__} {getattr(ox, '__version__', '')}\n",
        encoding="utf-8",
    )
    return {
        "result": ox.__name__,
        "figures": [],
        "artifacts": [note],
        "summary": f"adapter osmnx -> {ox.__name__}",
    }


if __name__ == "__main__":
    print(main(Path(__file__).resolve().parents[3] / "output" / "recipes" / "adapters" / "osmnx"))
