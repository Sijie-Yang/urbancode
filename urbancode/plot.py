"""Lazy map drawing for City and Layer. Imported only from plot()."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import numpy as np

from urbancode.errors import require_extra

FIGSIZE = (8.0, 5.5)
DPI = 120
NDVI_VMIN, NDVI_VMAX = -0.2, 0.8
SLOPE_VMIN, SLOPE_VMAX = 0.0, 45.0
FRACTION_VMIN, FRACTION_VMAX = 0.0, 1.0

VECTOR_STYLE = {
    "streets": {"color": "#4a4a4a", "linewidth": 1.1, "zorder": 2},
    "buildings": {
        "color": "#c4b8a8",
        "edgecolor": "#6e655c",
        "linewidth": 0.4,
        "zorder": 3,
    },
    "parks": {
        "color": "#7cb083",
        "edgecolor": "#2f5d38",
        "alpha": 0.85,
        "zorder": 2,
    },
    "pois": {"color": "#c0392b", "markersize": 40, "zorder": 3},
}


def _finite_values(values: Any) -> np.ndarray:
    array = np.asarray(values, dtype=float).ravel()
    return array[np.isfinite(array)]


def _robust_limits(finite: np.ndarray) -> tuple[float, float, bool]:
    if finite.size == 0:
        return 0.0, 1.0, False
    lo = float(np.min(finite))
    hi = float(np.max(finite))
    if lo == hi:
        pad = 0.5 if lo == 0 else abs(lo) * 0.05 or 0.5
        return lo - pad, hi + pad, True
    if finite.size >= 8:
        lo = float(np.nanpercentile(finite, 2))
        hi = float(np.nanpercentile(finite, 98))
        if lo == hi:
            lo = float(np.min(finite))
            hi = float(np.max(finite))
    return lo, hi, False


def indicator_style(
    name: str | None,
    *,
    unit: str | None = None,
    values: Any = None,
    **overrides: Any,
) -> dict[str, Any]:
    """Return cmap / vmin / vmax / label for an indicator name and unit.

    Explicit ``vmin`` / ``vmax`` / ``cmap`` / ``label`` in ``overrides`` win.
    """
    key = f"{name or ''} {unit or ''}".lower()
    finite = _finite_values(values) if values is not None else np.asarray([])
    auto_lo, auto_hi, constant = _robust_limits(finite) if finite.size else (None, None, False)
    label = overrides.get("label")
    cmap = overrides.get("cmap")
    vmin = overrides.get("vmin")
    vmax = overrides.get("vmax")

    if "ndvi" in key or "ndwi" in key:
        spec = {
            "cmap": cmap or "RdYlGn",
            "vmin": NDVI_VMIN if vmin is None else vmin,
            "vmax": NDVI_VMAX if vmax is None else vmax,
            "label": label or f"{name or 'index'} (dimensionless)",
        }
    elif any(token in key for token in ("area_fraction", "coverage", "probability", "_frac", "fraction")):
        spec = {
            "cmap": cmap or "YlGn",
            "vmin": FRACTION_VMIN if vmin is None else vmin,
            "vmax": FRACTION_VMAX if vmax is None else vmax,
            "label": label or f"{name or 'fraction'} (0–1)",
        }
    elif any(token in key for token in ("park_near", "distance", "_m", "metre", "meter")) and "ndvi" not in key:
        spec = {
            "cmap": cmap or "YlOrRd_r",
            "vmin": (0.0 if auto_lo is None else min(0.0, auto_lo)) if vmin is None else vmin,
            "vmax": (auto_hi if auto_hi is not None else 1.0) if vmax is None else vmax,
            "label": label or f"{name or 'distance'} (m)",
        }
    elif any(token in key for token in ("reachability", "count")):
        if "photo" in key:
            count_label = "photo count"
        elif "reach" in key:
            count_label = "node count"
        else:
            count_label = "count"
        spec = {
            "cmap": cmap or "viridis",
            "vmin": (0.0 if auto_lo is None else min(0.0, auto_lo)) if vmin is None else vmin,
            "vmax": (auto_hi if auto_hi is not None else 1.0) if vmax is None else vmax,
            "label": label or count_label,
        }
    elif "utci" in key or (unit or "").lower() in {"degree_celsius", "celsius", "degc"}:
        spec = {
            "cmap": cmap or "RdYlBu_r",
            "vmin": (auto_lo if auto_lo is not None else 0.0) if vmin is None else vmin,
            "vmax": (auto_hi if auto_hi is not None else 46.0) if vmax is None else vmax,
            "label": label or f"{name or 'UTCI'} (°C)",
        }
    elif any(
        token in key
        for token in (
            "thermal_affordance",
            "visual_comfort",
            "temp_intensity",
            "sun_intensity",
            "humidity_inference",
            "wind_inference",
            "greenery_rate",
            "shading_area",
            "score_0_5",
        )
    ) or (unit or "").lower() in {"score_0_5", "score"}:
        spec = {
            "cmap": cmap or "YlOrRd",
            "vmin": 0.0 if vmin is None else vmin,
            "vmax": 5.0 if vmax is None else vmax,
            "label": label or f"{name or 'score'} (0–5)",
        }
    elif "ndbi" in key:
        spec = {
            "cmap": cmap or "YlOrRd",
            "vmin": auto_lo if vmin is None else vmin,
            "vmax": auto_hi if vmax is None else vmax,
            "label": label or "NDBI (dimensionless)",
        }
    elif "slope" in key:
        spec = {
            "cmap": cmap or "magma",
            "vmin": SLOPE_VMIN if vmin is None else vmin,
            "vmax": SLOPE_VMAX if vmax is None else vmax,
            "label": label or "slope (°)",
        }
    elif "aspect" in key:
        spec = {
            "cmap": cmap or "twilight",
            "vmin": 0 if vmin is None else vmin,
            "vmax": 360 if vmax is None else vmax,
            "label": label or "aspect (° from north)",
        }
    elif "hillshade" in key:
        spec = {
            "cmap": cmap or "gray",
            "vmin": 0 if vmin is None else vmin,
            "vmax": 255 if vmax is None else vmax,
            "label": label or "hillshade",
        }
    else:
        spec = {
            "cmap": cmap or "viridis",
            "vmin": (auto_lo if auto_lo is not None else 0.0) if vmin is None else vmin,
            "vmax": (auto_hi if auto_hi is not None else 1.0) if vmax is None else vmax,
            "label": label or (f"{name} ({unit})" if name and unit else (name or "value")),
        }
    spec["constant"] = constant
    if constant:
        spec["label"] = f"{spec['label']} (constant field)"
    return spec


def plot_indicator_frame(ax, gdf: Any, *, column: str = "value", name: str | None = None, unit: str | None = None, **style: Any):
    """Choropleth on an existing axes using :func:`indicator_style`."""
    from urbancode.cartography import (
        apply_map_extent,
        decorate_map,
        draw_context,
        draw_indicator_frame,
        metric_crs,
        pop_carto,
        to_crs,
    )

    carto = pop_carto(style)
    context = carto.get("context")
    crs = metric_crs(context) if context is not None else None
    if context is not None:
        apply_map_extent(ax, context, crs)
        draw_context(
            ax,
            context,
            layers=carto.get("context_layers"),
            crs=crs,
            stage="under",
            under_indicator=True,
        )
        gdf = to_crs(gdf, crs)
    resolved = draw_indicator_frame(
        ax,
        gdf,
        column=column,
        name=name,
        unit=unit,
        alpha=style.pop("alpha", 0.72),
        unit_edges=carto.get("unit_edges", False),
        missing_style=carto.get("missing_style", "transparent"),
        **style,
    )
    if context is not None:
        draw_context(
            ax,
            context,
            layers=carto.get("context_layers"),
            crs=crs,
            stage="over",
        )
        decorate_map(
            ax,
            context,
            boundary=carto.get("boundary", True),
            show_scale=carto.get("show_scale", False),
            show_north=carto.get("show_north", False),
            locator=carto.get("locator", False),
            title=None,
        )
    else:
        ax.set_aspect("equal")
        ax.set_axis_off()
    return resolved


def plot_layer(
    layer: Any,
    *,
    title: str | None = None,
    overlay: Any = None,
    column: str | None = None,
    save: str | Path | None = None,
    basemap: bool = False,
    ax: Any = None,
    **style: Any,
) -> Path | Any:
    """Draw one layer, optionally with an overlay, and maybe save a PNG."""
    from urbancode.cartography import (
        apply_map_extent,
        decorate_map,
        draw_context,
        metric_crs,
        pop_carto,
    )

    carto = pop_carto(style)
    context = carto.get("context")
    own = ax is None
    if own:
        plt = _pyplot(save)
        fig, ax = plt.subplots(figsize=FIGSIZE)
    else:
        fig = ax.figure
    colorbar = None
    label = None
    crs = metric_crs(context) if context is not None else getattr(layer, "crs", None)
    if context is not None:
        apply_map_extent(ax, context, crs)
        draw_context(
            ax,
            context,
            layers=carto.get("context_layers"),
            crs=crs,
            stage="under",
            under_indicator=layer.kind in {"raster", "vector", "graph"},
        )
    if layer.kind == "raster":
        colorbar, label = _draw_raster(ax, layer, style)
        if overlay is not None:
            extra = _as_layer(overlay)
            if extra.kind == "raster":
                colorbar, label = _draw_raster(
                    ax, extra, {"alpha": 0.45, **style}, colorbar_from_overlay=True
                )
            else:
                _draw_vector_or_graph(ax, extra, _overlay_style(extra), target_crs=crs)
    elif layer.kind == "graph":
        colorbar, label = _draw_graph(ax, layer, column=column, target_crs=crs, **style)
    elif layer.kind == "vector":
        colorbar, label = _draw_vector(ax, layer, column=column, target_crs=crs, **style)
        if overlay is not None:
            _draw_vector_or_graph(ax, _as_layer(overlay), _overlay_style(_as_layer(overlay)), target_crs=crs)
    elif layer.kind in {"images", "table"}:
        if own:
            from matplotlib import pyplot as plt

            plt.close(fig)
        return plot_svi_panel([layer], title=title, save=save)
    else:
        raise TypeError(f"cannot plot layer kind {layer.kind!r}")

    if context is not None:
        draw_context(ax, context, layers=carto.get("context_layers"), crs=crs, stage="over")
        decorate_map(
            ax,
            context,
            boundary=carto.get("boundary", True),
            show_scale=carto.get("show_scale", own),
            show_north=carto.get("show_north", own),
            locator=carto.get("locator", False if not own else None),
            title=title if own else None,
            subtitle=carto.get("subtitle"),
            attribution=carto.get("attribution"),
        )
        title = None
    if basemap:
        _add_basemap(ax, crs)
    ax.set_aspect("equal")
    if own:
        return _finish(fig, ax, title, save, colorbar if carto.get("colorbar", True) else None, label)
    if carto.get("colorbar") and colorbar is not None:
        fig.colorbar(colorbar, ax=ax, fraction=0.046, label=label or "")
    if title:
        ax.set_title(title)
    return ax


def plot_city(
    city: Any,
    layers: Sequence[str] | None = None,
    *,
    title: str | None = None,
    save: str | Path | None = None,
    basemap: bool = False,
    ax: Any = None,
    **style: Any,
) -> Path | Any:
    """Draw named City layers on one axes (or a street-view + table panel)."""
    from urbancode.cartography import (
        CONTEXT_STYLE,
        DEFAULT_CONTEXT,
        decorate_map,
        draw_context,
        metric_crs,
        pop_carto,
    )

    carto = pop_carto(style)
    names = list(layers) if layers is not None else list(DEFAULT_CONTEXT)
    objs = []
    for name in names:
        try:
            objs.append(city.layer(name) if isinstance(name, str) else name)
        except Exception:
            continue
    kinds = {item.kind for item in objs}
    if kinds <= {"images", "table"} and any(item.kind == "images" for item in objs):
        return plot_svi_panel(objs, title=title or city.place, save=save)

    own = ax is None
    if own:
        plt = _pyplot(save)
        fig, ax = plt.subplots(figsize=FIGSIZE)
    else:
        fig = ax.figure
    colorbar = None
    label = None
    target_crs = metric_crs(city)
    draw_context(ax, city, layers=names, crs=target_crs, stage="all")
    for item in objs:
        if item.kind == "raster":
            colorbar, label = _draw_raster(ax, item, style)
        elif item.name not in CONTEXT_STYLE and item.kind == "graph":
            cb, lab = _draw_graph(ax, item, target_crs=target_crs, **style)
            colorbar = cb or colorbar
            label = lab or label
    if basemap:
        _add_basemap(ax, target_crs)
    decorate_map(
        ax,
        city,
        boundary=carto.get("boundary", True),
        show_scale=carto.get("show_scale", True),
        show_north=carto.get("show_north", True),
        locator=carto.get("locator"),
        scale_length=carto.get("scale_length", 500),
        title=title if own else None,
        subtitle=carto.get("subtitle"),
        attribution=carto.get("attribution"),
    )
    if own:
        return _finish(fig, ax, None, save, colorbar if carto.get("colorbar") else None, label)
    if title:
        ax.set_title(title, loc="left", fontsize=10)
    return ax


def plot_svi_panel(
    layers: Sequence[Any],
    *,
    title: str | None = None,
    save: str | Path | None = None,
) -> Path | Any:
    """Street photo plus comfort metadata (no model inference)."""
    plt = _pyplot(save)
    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE)
    photo = next((item for item in layers if item.kind == "images"), None)
    table = next((item for item in layers if item.kind == "table"), None)
    if photo is None or not photo.path:
        raise ValueError("street-view plot needs an images layer with a path")
    if table is None:
        plt.close(fig)
        fig, ax = plt.subplots(figsize=FIGSIZE)
        ax.imshow(plt.imread(photo.path))
        ax.set_axis_off()
        if title:
            ax.set_title(title)
        if save:
            path = Path(save)
            path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.5)
            plt.close(fig)
            return path
        return fig
    axes[0].imshow(plt.imread(photo.path))
    axes[0].set_axis_off()
    axes[0].set_title("Punggol street-level photo")
    axes[1].axis("off")
    axes[1].text(0.05, 0.55, _comfort_text(photo, table, title), va="center", fontsize=10)
    if save:
        path = Path(save)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.5)
        plt.close(fig)
        return path
    return fig


def _pyplot(save: str | Path | None):
    mpl = require_extra("matplotlib", "viz")
    if save is not None:
        mpl.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "figure.figsize": FIGSIZE,
            "figure.dpi": DPI,
            "axes.titlesize": 12,
        }
    )
    return plt


def _finish(fig, ax, title, save, colorbar, label) -> Path | Any:
    if title:
        ax.set_title(title)
    ax.set_axis_off()
    if colorbar is not None:
        bar = fig.colorbar(colorbar, ax=ax, fraction=0.035, label=label or "")
        if label and "aspect" in str(label).lower():
            bar.set_ticks([0, 90, 180, 270, 360])
            bar.set_ticklabels(["N", "E", "S", "W", "N"])
    if save is not None:
        path = Path(save)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.5)
        from matplotlib import pyplot as plt

        plt.close(fig)
        return path
    return fig


def _as_layer(value: Any) -> Any:
    from urbancode.city import Layer

    if isinstance(value, Layer):
        return value
    if hasattr(value, "geometry"):
        return Layer(name="overlay", kind="vector", data=value, crs=getattr(value, "crs", None))
    if hasattr(value, "nodes") and hasattr(value, "edges"):
        return Layer(name="overlay", kind="graph", data=value)
    if isinstance(value, np.ndarray):
        return Layer(name="overlay", kind="raster", data=value)
    raise TypeError(f"overlay must be a Layer, GeoDataFrame, or graph; got {type(value).__name__}")


def _overlay_style(layer: Any) -> dict[str, Any]:
    if layer.kind == "vector":
        geom = None
        data = layer.data
        if data is not None and len(data) and hasattr(data, "geom_type"):
            geom = str(data.geom_type.iloc[0])
        if layer.name == "buildings" or (geom and "Polygon" in geom):
            return {
                "edgecolor": "k",
                "facecolor": "none",
                "linewidth": 0.4,
                "alpha": 0.6,
                "zorder": 4,
            }
    return dict(VECTOR_STYLE.get(layer.name, {"color": "k", "linewidth": 0.4}))


def _draw_raster(ax, layer, style: dict[str, Any], colorbar_from_overlay: bool = False):
    array, transform, _crs = _raster_payload(layer)
    defaults = _raster_defaults(layer)
    cmap = style.get("cmap", defaults["cmap"])
    vmin = style.get("vmin", defaults.get("vmin"))
    vmax = style.get("vmax", defaults.get("vmax"))
    alpha = style.get("alpha", 1.0)
    extent = _extent(transform, array)
    image = ax.imshow(
        array,
        extent=extent,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        alpha=alpha,
        origin="upper",
        zorder=1 if not colorbar_from_overlay else 2,
    )
    label = style.get("label") or defaults.get("label") or layer.name
    return image, label


def _raster_payload(layer) -> tuple[np.ndarray, Any, Any]:
    data = layer.data
    if data is None and layer.path:
        return _read_first_band(layer.path)
    if isinstance(data, (str, Path)) and Path(data).exists():
        return _read_first_band(data)
    if hasattr(data, "rio"):
        values = np.asarray(data.values)
        if values.ndim == 3:
            values = values[0]
        return values, data.rio.transform(), data.rio.crs
    if isinstance(data, np.ndarray):
        transform = layer.metadata.get("transform")
        if transform is None:
            raise ValueError(
                f"layer {layer.name!r} has no transform; cannot place it on a map"
            )
        return np.asarray(data), transform, layer.crs
    if layer.path:
        return _read_first_band(layer.path)
    raise ValueError(f"layer {layer.name!r} has no raster to plot")


def _read_first_band(path: str | Path) -> tuple[np.ndarray, Any, Any]:
    rasterio = require_extra("rasterio", "imagery")
    with rasterio.open(path) as src:
        return src.read(1), src.transform, src.crs


def _extent(transform: Any, array: np.ndarray) -> tuple[float, float, float, float]:
    from urbancode.imagery.source import as_affine

    affine = as_affine(transform)
    height, width = array.shape[-2], array.shape[-1]
    left = float(affine.c)
    top = float(affine.f)
    return left, left + float(affine.a) * width, top + float(affine.e) * height, top


def _raster_defaults(layer) -> dict[str, Any]:
    meta = layer.metadata or {}
    values = None
    try:
        array, _transform, _crs = _raster_payload(layer)
        values = array
    except Exception:
        values = None
    return indicator_style(
        layer.name,
        unit=meta.get("unit"),
        values=values,
    )


def _draw_vector(ax, layer, column: str | None = None, target_crs: Any = None, **style: Any):
    from urbancode.cartography import to_crs

    gdf = to_crs(layer.data, target_crs)
    if gdf is None or not hasattr(gdf, "plot"):
        raise TypeError(f"vector layer {layer.name!r} has no GeoDataFrame")
    column = column or (layer.metadata or {}).get("column")
    defaults = dict(VECTOR_STYLE.get(layer.name, {}))
    if column and column in gdf.columns:
        meta = layer.metadata or {}
        resolved = indicator_style(
            layer.name,
            unit=meta.get("unit"),
            values=gdf[column],
            **{k: style[k] for k in ("cmap", "vmin", "vmax", "label") if k in style},
        )
        plot_kw = {
            "column": column,
            "cmap": resolved["cmap"],
            "vmin": resolved["vmin"],
            "vmax": resolved["vmax"],
            "edgecolor": style.get("edgecolor", "#2f5d38"),
            "legend": True,
            "legend_kwds": {"label": resolved["label"]},
            "zorder": 2,
        }
        extra = {k: v for k, v in style.items() if k not in {"cmap", "vmin", "vmax", "label"}}
        gdf.plot(ax=ax, **plot_kw, **extra)
        return None, resolved["label"]
    merged = {**defaults, **style}
    gdf.plot(ax=ax, **merged)
    return None, None


def _draw_vector_or_graph(ax, layer, style: dict[str, Any], target_crs: Any = None) -> None:
    if layer.kind == "graph":
        _draw_graph(ax, layer, **style)
        return
    gdf = layer.data
    if gdf is None:
        return
    if target_crs is not None and getattr(gdf, "crs", None) is not None:
        if str(gdf.crs) != str(target_crs):
            gdf = gdf.to_crs(target_crs)
    if style.get("facecolor") == "none":
        gdf.boundary.plot(ax=ax, **{k: v for k, v in style.items() if k != "facecolor"})
        return
    gdf.plot(ax=ax, **style)


def _draw_graph(ax, layer, column: str | None = None, target_crs: Any = None, **style: Any):
    from urbancode.cartography import graph_edges_frame

    graph = layer.data
    if graph is None:
        raise TypeError(f"graph layer {layer.name!r} has no graph")
    column = column or (layer.metadata or {}).get("column")
    color = style.get("color", "#888888")
    linewidth = style.get("linewidth", 0.8)
    edges = graph_edges_frame(layer, target_crs)
    if edges is not None and len(edges):
        edges.plot(ax=ax, color=color, linewidth=linewidth, zorder=1)
    if not column:
        return None, None
    gpd = __import__("geopandas", fromlist=["GeoDataFrame"])
    from shapely.geometry import Point

    rows = []
    values = []
    for node in graph.nodes:
        x, y = _node_xy(graph, node)
        rows.append(Point(x, y))
        raw = graph.nodes[node].get(column, 0.0)
        values.append(float(raw) if raw is not None else 0.0)
    nodes = gpd.GeoDataFrame({"value": values}, geometry=rows, crs=layer.crs or "EPSG:4326")
    if target_crs is not None:
        nodes = nodes.to_crs(target_crs)
    xs = nodes.geometry.x
    ys = nodes.geometry.y
    resolved = indicator_style(
        column or layer.name,
        unit=(layer.metadata or {}).get("unit"),
        values=values,
        **{k: style[k] for k in ("cmap", "vmin", "vmax", "label") if k in style},
    )
    scatter = ax.scatter(
        xs,
        ys,
        c=values,
        cmap=resolved["cmap"],
        s=style.get("s", 12),
        vmin=resolved["vmin"],
        vmax=resolved["vmax"],
        zorder=2,
    )
    return scatter, resolved["label"]


def _node_xy(graph, node) -> tuple[float, float]:
    data = graph.nodes[node]
    if "x" not in data or "y" not in data:
        raise ValueError(
            f"graph node {node!r} is missing x/y; UrbanCode plots OSM-style graphs"
        )
    return float(data["x"]), float(data["y"])


def _add_basemap(ax, crs: Any) -> None:
    cx = require_extra("contextily", "imagery")
    cx.add_basemap(ax, crs=crs or "EPSG:4326", source=cx.providers.CartoDB.Positron)


def _comfort_text(photo, table, title: str | None) -> str:
    import math

    place = title or "Punggol, Singapore"
    credit = photo.metadata or {}
    row = None
    if table is not None and table.data is not None and len(table.data):
        row = table.data.iloc[0]
    thermal = row.get("thermal_comfort") if row is not None else None
    visual = row.get("visual_comfort") if row is not None else None
    if (
        thermal == thermal
        and visual == visual
        and not (isinstance(thermal, float) and math.isnan(float(thermal)))
    ):
        scores = (
            f"thermal_comfort: {float(thermal):.2f}\n"
            f"visual_comfort: {float(visual):.2f}\n"
            f"model: {row.get('model_version', 'n/a')}\n"
            f"generated: {row.get('generated_at', 'n/a')}\n"
        )
    else:
        scores = (
            "TCIS scores are not precomputed here.\n"
            "Run examples/live/03_streetview_predict.py\n"
        )
    return (
        f"{place}\n\n{scores}\n"
        f"photo: {credit.get('title') or (row.get('Filename', '') if row is not None else '')}\n"
        f"license: {credit.get('license') or (row.get('photo_license', '') if row is not None else '')}\n"
    )
