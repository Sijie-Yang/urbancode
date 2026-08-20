"""Internal map helpers. Public entry points remain City/Layer/IndicatorResult.plot."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

CARTO_KEYS = {
    "ax",
    "context",
    "context_layers",
    "boundary",
    "unit_edges",
    "missing_style",
    "show_scale",
    "show_north",
    "locator",
    "attribution",
    "legend",
    "colorbar",
    "subtitle",
    "scale_length",
}

DEFAULT_CONTEXT = ("water", "parks", "landuse", "buildings", "streets")
UNDER_LAYERS = ("landuse", "water", "parks", "buildings")
OVER_LAYERS = ("streets", "pois")

CONTEXT_STYLE = {
    "water": {
        "color": "#9ecae1",
        "edgecolor": "#6baed6",
        "linewidth": 0.35,
        "alpha": 0.95,
        "zorder": 1,
    },
    "parks": {
        "color": "#c7e9c0",
        "edgecolor": "#74c476",
        "linewidth": 0.35,
        "alpha": 0.9,
        "zorder": 2,
    },
    "landuse": {
        "color": "#f0e6d2",
        "edgecolor": "#d9c7a5",
        "linewidth": 0.15,
        "alpha": 0.35,
        "zorder": 0,
    },
    "buildings": {
        "facecolor": "#d8d0c6",
        "edgecolor": "#6e655c",
        "linewidth": 0.25,
        "alpha": 0.85,
        "zorder": 3,
    },
    "streets": {"color": "#4a4a4a", "linewidth": 0.55, "zorder": 7},
    "pois": {"color": "#c0392b", "markersize": 8, "zorder": 8},
}

UNDER_INDICATOR_STYLE = {
    "buildings": {
        "facecolor": "none",
        "edgecolor": "#6e655c",
        "linewidth": 0.2,
        "alpha": 0.55,
        "zorder": 3,
    },
    "parks": {
        "facecolor": "none",
        "edgecolor": "#2f5d38",
        "linewidth": 0.45,
        "alpha": 0.9,
        "zorder": 4,
    },
}


def pop_carto(style: dict[str, Any]) -> dict[str, Any]:
    carto = {key: style.pop(key) for key in list(style) if key in CARTO_KEYS}
    carto.setdefault("context_layers", DEFAULT_CONTEXT)
    carto.setdefault("boundary", True)
    carto.setdefault("unit_edges", False)
    carto.setdefault("missing_style", "transparent")
    carto.setdefault("show_scale", True)
    carto.setdefault("show_north", True)
    carto.setdefault("colorbar", True)
    carto.setdefault("legend", True)
    carto.setdefault("scale_length", 500)
    return carto


def metric_crs(source: Any) -> str:
    area = getattr(source, "study_area", None)
    if area is not None and getattr(area, "metric_crs", None):
        return str(area.metric_crs)
    meta = getattr(source, "metadata", None) or {}
    if meta.get("metric_crs"):
        return str(meta["metric_crs"])
    crs = getattr(source, "crs", None)
    if crs is not None and "4326" not in str(crs):
        return str(crs)
    return "EPSG:4326"


def to_crs(frame: Any, crs: str | None) -> Any:
    if frame is None or crs is None or not hasattr(frame, "to_crs"):
        return frame
    if getattr(frame, "crs", None) is None:
        return frame
    if str(frame.crs) == str(crs):
        return frame
    return frame.to_crs(crs)


def study_frame(city: Any, crs: str | None = None) -> Any:
    from shapely.geometry import box

    gpd = _geopandas()
    crs = crs or metric_crs(city)
    area = getattr(city, "study_area", None)
    geom = None
    src_crs = "EPSG:4326"
    if area is not None:
        if getattr(area, "geometry", None) is not None:
            geom = area.geometry
            src_crs = getattr(area, "geographic_crs", "EPSG:4326")
        elif getattr(area, "boundary", None) is not None:
            geom = area.boundary
            src_crs = getattr(area, "geographic_crs", "EPSG:4326")
        elif getattr(area, "bbox", None) is not None:
            geom = box(*area.bbox)
    if geom is None:
        bbox = (getattr(city, "metadata", None) or {}).get("bbox")
        if bbox:
            geom = box(*bbox)
    if geom is None:
        return None
    if hasattr(geom, "geometry"):
        frame = geom if hasattr(geom, "to_crs") else gpd.GeoDataFrame(geometry=list(geom.geometry), crs=src_crs)
    else:
        frame = gpd.GeoDataFrame(geometry=[geom], crs=src_crs)
    return to_crs(frame, crs)


def apply_map_extent(ax, source: Any, crs: str | None = None, pad: float = 0.03) -> None:
    frame = study_frame(source, crs or metric_crs(source))
    if frame is None or frame.empty:
        ax.set_aspect("equal")
        return
    minx, miny, maxx, maxy = frame.total_bounds
    dx = (maxx - minx) * pad
    dy = (maxy - miny) * pad
    ax.set_xlim(minx - dx, maxx + dx)
    ax.set_ylim(miny - dy, maxy + dy)
    ax.set_aspect("equal")
    ax.set_facecolor("#f4f1ea")


def draw_context(
    ax,
    city: Any,
    *,
    layers: Sequence[str] | None = None,
    crs: str | None = None,
    stage: str = "all",
    under_indicator: bool = False,
) -> None:
    names = list(layers or DEFAULT_CONTEXT)
    if stage == "under":
        names = [name for name in UNDER_LAYERS if name in names]
    elif stage == "over":
        names = [name for name in OVER_LAYERS if name in names]
    crs = crs or metric_crs(city)
    for name in names:
        layer = _layer(city, name)
        if layer is None:
            continue
        style = dict(CONTEXT_STYLE.get(name, {}))
        if under_indicator and name in UNDER_INDICATOR_STYLE:
            style = dict(UNDER_INDICATOR_STYLE[name])
        _draw_named(ax, layer, name, crs, style)


def draw_boundary(ax, city: Any, *, crs: str | None = None) -> None:
    frame = study_frame(city, crs or metric_crs(city))
    if frame is None or frame.empty:
        return
    frame.boundary.plot(ax=ax, color="k", linewidth=1.15, zorder=12)


def draw_scale_bar(ax, length: float = 500) -> None:
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    span = abs(x1 - x0)
    # Geographic axes span a few degrees; a 500 m bar would be 500°.
    if span < 50 or span > 50_000:
        return
    if length > span * 0.45:
        length = max(100.0, span * 0.25)
    pad_x = (x1 - x0) * 0.05
    pad_y = (y1 - y0) * 0.05
    x = x0 + pad_x
    y = y0 + pad_y
    ax.plot([x, x + length], [y, y], color="k", linewidth=1.8, solid_capstyle="butt", zorder=20)
    ax.plot([x, x], [y - pad_y * 0.15, y + pad_y * 0.15], color="k", linewidth=1.2, zorder=20)
    ax.plot(
        [x + length, x + length],
        [y - pad_y * 0.15, y + pad_y * 0.15],
        color="k",
        linewidth=1.2,
        zorder=20,
    )
    ax.text(
        x + length / 2.0,
        y + pad_y * 0.35,
        f"{int(length)} m",
        ha="center",
        va="bottom",
        fontsize=7,
        zorder=20,
    )


def draw_north_arrow(ax) -> None:
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    x = x1 - (x1 - x0) * 0.08
    y = y1 - (y1 - y0) * 0.12
    ax.annotate(
        "N",
        xy=(x, y),
        xytext=(x, y - (y1 - y0) * 0.07),
        ha="center",
        va="center",
        fontsize=8,
        arrowprops={"arrowstyle": "-|>", "color": "k", "lw": 1.0},
        zorder=20,
    )


def draw_locator_inset(ax, city: Any, locator: Any = None) -> None:
    frame = _locator_frame(city, locator)
    pocket = study_frame(city, "EPSG:4326")
    if frame is None or frame.empty:
        return
    inset = ax.inset_axes((0.68, 0.04, 0.28, 0.28))
    frame.plot(ax=inset, facecolor="#f7f7f7", edgecolor="#333333", linewidth=0.6, zorder=1)
    if pocket is not None and not pocket.empty:
        pocket.plot(ax=inset, facecolor="none", edgecolor="#c0392b", linewidth=1.3, zorder=2)
    inset.set_aspect("equal")
    inset.set_xticks([])
    inset.set_yticks([])
    for spine in inset.spines.values():
        spine.set_linewidth(0.6)


def decorate_map(
    ax,
    city: Any | None,
    *,
    boundary: bool = True,
    show_scale: bool = True,
    show_north: bool = True,
    locator: Any = None,
    scale_length: float = 500,
    title: str | None = None,
    subtitle: str | None = None,
    attribution: str | None = None,
) -> None:
    if city is not None:
        apply_map_extent(ax, city)
        if boundary:
            draw_boundary(ax, city)
        if locator is not False:
            draw_locator_inset(ax, city, locator)
    if show_scale:
        draw_scale_bar(ax, length=scale_length)
    if show_north:
        draw_north_arrow(ax)
    if title:
        ax.set_title(title, loc="left", fontsize=10, pad=8)
    if subtitle:
        ax.text(
            0.0,
            1.01,
            subtitle,
            transform=ax.transAxes,
            fontsize=7,
            color="#444444",
            va="bottom",
        )
    if attribution:
        ax.text(
            0.0,
            -0.04,
            attribution,
            transform=ax.transAxes,
            fontsize=6,
            color="#666666",
            va="top",
        )
    ax.set_axis_off()


def draw_indicator_frame(
    ax,
    gdf: Any,
    *,
    column: str = "value",
    name: str | None = None,
    unit: str | None = None,
    alpha: float = 0.72,
    unit_edges: bool = False,
    missing_style: str = "transparent",
    **style: Any,
) -> dict[str, Any]:
    from urbancode.plot import indicator_style

    if gdf is None or not hasattr(gdf, "plot"):
        raise TypeError("draw_indicator_frame needs a GeoDataFrame")
    resolved = indicator_style(
        name,
        unit=unit,
        values=gdf[column] if column in gdf.columns else None,
        **{key: style[key] for key in ("cmap", "vmin", "vmax", "label") if key in style},
    )
    missing = None
    if "coverage" in gdf.columns:
        missing = gdf["coverage"].fillna(0) <= 0
    plotted = gdf
    if missing is not None and bool(missing.any()):
        if missing_style == "hatch":
            gdf.loc[missing].plot(
                ax=ax,
                facecolor="none",
                edgecolor="#888888",
                hatch="////",
                linewidth=0.2,
                zorder=2,
            )
        plotted = gdf.loc[~missing]
    if len(plotted):
        edge = style.get("edgecolor", "#f7f7f7" if unit_edges else "none")
        width = style.get("linewidth", 0.15 if unit_edges else 0.0)
        plotted.plot(
            ax=ax,
            column=column,
            cmap=resolved["cmap"],
            vmin=resolved["vmin"],
            vmax=resolved["vmax"],
            edgecolor=edge,
            linewidth=width,
            alpha=style.get("alpha", alpha),
            legend=False,
            zorder=5,
        )
    ax.set_aspect("equal")
    return resolved


def graph_edges_frame(layer: Any, crs: str | None = None) -> Any:
    gpd = _geopandas()
    from shapely.geometry import LineString

    graph = layer.data
    if graph is None:
        return None
    lines = []
    for u, v, *_rest in graph.edges(keys=True) if graph.is_multigraph() else ((a, b, 0) for a, b in graph.edges):
        x0, y0 = _xy(graph, u)
        x1, y1 = _xy(graph, v)
        lines.append(LineString([(x0, y0), (x1, y1)]))
    src = layer.crs or "EPSG:4326"
    frame = gpd.GeoDataFrame(geometry=lines, crs=src)
    return to_crs(frame, crs)


def colorbar(fig, ax, resolved: dict[str, Any]) -> None:
    import matplotlib.pyplot as plt

    sm = plt.cm.ScalarMappable(
        cmap=resolved["cmap"],
        norm=plt.Normalize(resolved["vmin"], resolved["vmax"]),
    )
    fig.colorbar(sm, ax=ax, fraction=0.046, pad=0.02, label=resolved.get("label") or "")


def attach_locator(city: Any, root: str | Path | None = None) -> Any:
    path = None
    if root is not None:
        candidate = Path(root) / "context" / "locator_boundary.gpkg"
        if candidate.is_file():
            path = candidate
    meta = getattr(city, "metadata", None) or {}
    if path is None and meta.get("locator"):
        path = Path(meta["locator"])
    if path is not None and path.is_file():
        city.metadata["locator"] = str(path)
    return city


def _locator_frame(city: Any, locator: Any) -> Any:
    gpd = _geopandas()
    if locator is False:
        return None
    if locator is None or locator is True:
        locator = (getattr(city, "metadata", None) or {}).get("locator")
    if locator is None:
        return None
    if hasattr(locator, "geometry"):
        frame = locator if hasattr(locator, "to_crs") else gpd.GeoDataFrame(geometry=list(locator.geometry), crs="EPSG:4326")
        return to_crs(frame, "EPSG:4326")
    path = Path(locator)
    if not path.is_file():
        return None
    return gpd.read_file(path).to_crs("EPSG:4326")


def _layer(city: Any, name: str) -> Any:
    layers = getattr(city, "layers", None) or {}
    layer = layers.get(name) if hasattr(layers, "get") else None
    if layer is None:
        try:
            return city.layer(name)
        except Exception:
            return None
    if getattr(layer, "lazy", False) and getattr(layer, "data", None) is None:
        from urbancode.city import _materialize_layer

        return _materialize_layer(layer)
    return layer


def _draw_named(ax, layer, name: str, crs: str, style: dict[str, Any]) -> None:
    if layer.kind == "graph":
        frame = graph_edges_frame(layer, crs)
        if frame is None or frame.empty:
            return
        frame.plot(ax=ax, **{k: v for k, v in style.items() if k != "markersize"})
        return
    frame = to_crs(layer.data, crs)
    if frame is None or not hasattr(frame, "plot") or len(frame) == 0:
        return
    frame.plot(ax=ax, **style)


def _xy(graph, node) -> tuple[float, float]:
    data = graph.nodes[node]
    return float(data["x"]), float(data["y"])


def _geopandas():
    from urbancode.errors import require_extra

    return require_extra("geopandas", "vector")
