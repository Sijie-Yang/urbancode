"""Render tutorial figures into docs/source/_static/tutorials.

Read the Docs does not run this script. ``scripts/build_gallery.py``
calls it so one local command refreshes every committed PNG.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import urbancode as uc

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "examples" / "data" / "punggol_pocket"
DEFAULT_OUT = ROOT / "docs" / "source" / "_static" / "tutorials"
PLACE = "Punggol, Singapore"


def main(output: str | Path | None = None) -> dict[str, Path]:
    out = Path(output) if output else DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)
    city = uc.load(DATA)
    written: dict[str, Path] = {}

    written["streets"] = city.plot(
        layers=["streets"],
        title=f"{PLACE} — streets",
        save=out / "network_streets.png",
    )
    written["buildings"] = city.plot(
        layers=["buildings"],
        title=f"{PLACE} — buildings",
        save=out / "network_buildings.png",
    )
    written["streets_buildings"] = city.plot(
        layers=["streets", "buildings"],
        title=f"{PLACE} — streets and buildings",
        save=out / "network_streets_buildings.png",
    )
    written["parks_pois"] = city.plot(
        layers=["parks", "pois"],
        title=f"{PLACE} — parks and POIs",
        save=out / "network_parks_pois.png",
    )
    written["streets_parks"] = city.plot(
        layers=["streets", "parks"],
        title=f"{PLACE} — streets and parks",
        save=out / "network_streets_parks.png",
    )

    between = uc.network.centrality(city["streets"], metric="betweenness", radius=500)
    written["betweenness"] = between.plot(
        title=f"{PLACE} — betweenness (500 m)",
        save=out / "network_betweenness.png",
    )
    close = uc.network.centrality(city["streets"], metric="closeness", radius=500)
    written["closeness"] = close.plot(
        title=f"{PLACE} — closeness (500 m)",
        save=out / "network_closeness.png",
    )
    reach = uc.network.accessibility(city["streets"], radius=500, metric="reachability")
    written["reachability"] = reach.plot(
        title=f"{PLACE} — reachability (500 m)",
        save=out / "network_reachability.png",
    )
    clustering = uc.network.clustering(city["streets"], radius=500)
    written["clustering"] = clustering.plot(
        title=f"{PLACE} — clustering (experimental)",
        save=out / "network_clustering.png",
    )
    efficiency = uc.network.local_efficiency(city["streets"], radius=500)
    written["efficiency"] = efficiency.plot(
        title=f"{PLACE} — local efficiency (experimental)",
        save=out / "network_efficiency.png",
    )

    ndvi = uc.imagery.ndvi(city["sentinel2"])
    written["ndvi"] = ndvi.plot(
        overlay=city["buildings"],
        title=f"{PLACE} — NDVI",
        save=out / "imagery_ndvi.png",
    )
    ndbi = uc.imagery.ndbi(city["sentinel2"])
    written["ndbi"] = ndbi.plot(
        overlay=city["buildings"],
        title=f"{PLACE} — NDBI",
        save=out / "imagery_ndbi.png",
    )
    hillshade = uc.imagery.hillshade(city["dem"])
    slope = uc.imagery.slope(city["dem"])
    written["hillshade"] = hillshade.plot(
        title=f"{PLACE} — hillshade",
        save=out / "imagery_hillshade.png",
    )
    written["slope"] = slope.plot(
        title=f"{PLACE} — slope",
        save=out / "imagery_slope.png",
    )
    aspect = uc.imagery.aspect(city["dem"])
    written["aspect"] = aspect.plot(
        title=f"{PLACE} — aspect",
        save=out / "imagery_aspect.png",
    )
    written["terrain"] = hillshade.plot(
        overlay=slope,
        title=f"{PLACE} — hillshade and slope",
        save=out / "imagery_terrain.png",
    )
    stats = uc.imagery.zonal_stats(ndvi, city["parks"], metrics=["mean"])
    written["zonal"] = stats.plot(
        column="mean",
        title=f"{PLACE} — park NDVI",
        save=out / "imagery_zonal_ndvi.png",
    )

    written["streetview_photo"] = city.plot(
        layers=["streetview"],
        title=f"{PLACE} — street-level photo",
        save=out / "streetview_photo.png",
    )
    written["streetview_panel"] = city.plot(
        layers=["streetview", "comfort"],
        title=PLACE,
        save=out / "streetview_panel.png",
    )

    for name, path in written.items():
        print(f"{name} -> {path}")
    return written


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUT),
        help="Directory for PNG outputs",
    )
    args = parser.parse_args()
    main(args.output)
