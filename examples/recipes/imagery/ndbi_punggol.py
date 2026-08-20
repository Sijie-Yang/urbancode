from __future__ import annotations

from pathlib import Path

from examples.recipes.imagery._indices import run_indices


def main(out_dir: str | Path) -> dict:
    return run_indices(out_dir)


if __name__ == "__main__":
    print(main(Path("examples/output/recipes/imagery/ndbi_punggol"))["summary"])
