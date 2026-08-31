"""Live OSM fetch on a ~0.01° bbox. Default tests skip this script."""

from __future__ import annotations

from pathlib import Path

TINY_BBOX = (103.905, 1.400, 103.915, 1.410)


def main(out_dir: str | Path, *, add_basemap: bool = False) -> dict[str, Path]:
    import urbancode as uc

    city = uc.network.fetch(
        place="Punggol, Singapore",
        bbox=TINY_BBOX,
        layers=["streets"],
        network_type="walk",
    )
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dest = city.to_dir(out / "live_network")
    del add_basemap
    return {"city": dest}


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
