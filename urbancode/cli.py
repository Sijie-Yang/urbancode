"""UrbanCode command-line interface. Commands call the Python API only."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from urbancode._version import __version__

app = typer.Typer(
    name="uc",
    help="UrbanCode: street view, imagery, and OSM urban analysis.",
    no_args_is_help=True,
)
network_app = typer.Typer(help="OSM / street-network commands.")
imagery_app = typer.Typer(help="Satellite and raster commands.")
svi_app = typer.Typer(help="Street-view imagery (SVI) commands.")
app.add_typer(network_app, name="network")
app.add_typer(imagery_app, name="imagery")
app.add_typer(svi_app, name="svi")
app.add_typer(svi_app, name="streetview", hidden=True)


def _split_csv(value: Optional[str]) -> list[str] | None:
    if value is None:
        return None
    return [part.strip() for part in value.split(",") if part.strip()]


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"urbancode {__version__}")
        raise typer.Exit()


@app.callback()
def _root(
    version: bool = typer.Option(
        False,
        "--version",
        help="Print the UrbanCode version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    return None


@app.command("fetch")
def fetch_cmd(
    place: str = typer.Option(..., "--place", help="Place name to geocode."),
    modalities: Optional[str] = typer.Option(
        None, "--modalities", help="Comma-separated presets: osm,satellite,terrain."
    ),
    layers: Optional[str] = typer.Option(
        None, "--layers", help="Comma-separated layer names."
    ),
    out: Path = typer.Option(Path("city"), "--out", help="Output directory."),
    on_error: str = typer.Option("raise", "--on-error", help="raise|warn|ignore"),
    refresh: bool = typer.Option(False, "--refresh"),
) -> None:
    """Download selected modalities into a City directory."""
    from urbancode.fetch import fetch

    city = fetch(
        place,
        modalities=_split_csv(modalities),
        layers=_split_csv(layers),
        out=out,
        on_error=on_error,
        refresh=refresh,
    )
    typer.echo(f"Wrote {len(city.keys())} layers to {out}")
    if city.errors:
        typer.echo(f"Errors: {len(city.errors)}")


@network_app.command("fetch")
def network_fetch_cmd(
    place: str = typer.Option(..., "--place"),
    layers: str = typer.Option("streets", "--layers"),
    network_type: str = typer.Option("walk", "--network-type"),
    source: str = typer.Option("osm", "--source"),
    out: Path = typer.Option(Path("city.gpkg"), "--out"),
    on_error: str = typer.Option("raise", "--on-error"),
) -> None:
    """Download OSM vector layers."""
    from urbancode.network.fetch import fetch as network_fetch

    city = network_fetch(
        place=place,
        layers=_split_csv(layers) or ["streets"],
        network_type=network_type,
        source=source,
        on_error=on_error,
    )
    if out.suffix.lower() == ".gpkg":
        city.to_gpkg(out)
    else:
        city.to_dir(out)
    typer.echo(f"Wrote network layers to {out}")


@imagery_app.command("fetch")
def imagery_fetch_cmd(
    place: Optional[str] = typer.Option(None, "--place"),
    bbox: Optional[str] = typer.Option(
        None, "--bbox", help="west,south,east,north in WGS84"
    ),
    layers: str = typer.Option("sentinel2", "--layers"),
    time: Optional[str] = typer.Option(None, "--time", help="STAC datetime interval"),
    cloud: int = typer.Option(20, "--cloud"),
    composite: str = typer.Option("single", "--composite"),
    max_pixels: int = typer.Option(25_000_000, "--max-pixels"),
    out: Path = typer.Option(Path("city"), "--out"),
    on_error: str = typer.Option("raise", "--on-error"),
) -> None:
    """Download or derive raster layers. Geocodes --place via geopy, not osmnx."""
    from urbancode.imagery import fetch as imagery_fetch

    bounds = None
    if bbox:
        parts = [float(p.strip()) for p in bbox.split(",")]
        if len(parts) != 4:
            raise typer.BadParameter("bbox must be west,south,east,north")
        bounds = (parts[0], parts[1], parts[2], parts[3])
    city = imagery_fetch(
        place=place,
        bbox=bounds,
        layers=_split_csv(layers) or ["sentinel2"],
        time=time,
        cloud=cloud,
        composite=composite,
        max_pixels=max_pixels,
        on_error=on_error,
    )
    city.to_dir(out)
    typer.echo(f"Wrote imagery layers to {out}")


@svi_app.command("comfort")
def svi_comfort_cmd(
    path: Path = typer.Argument(..., help="Image file or folder."),
    out: Path = typer.Option(Path("comfort.csv"), "--out"),
    mode: Optional[str] = typer.Option(None, "--mode", help="image|folder"),
) -> None:
    """Run TCIS comfort prediction."""
    from urbancode.streetview.perception import comfort

    resolved_mode = mode or ("folder" if path.is_dir() else "image")
    frame = comfort(str(path), mode=resolved_mode)
    frame.to_csv(out, index=False)
    typer.echo(f"Wrote {len(frame)} rows to {out}")
