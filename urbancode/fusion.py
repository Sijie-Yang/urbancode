"""Aggregate Layers onto AnalysisUnits."""

from __future__ import annotations

from typing import Any

import numpy as np

from urbancode.city import Layer
from urbancode.errors import require_extra
from urbancode.indicators import IndicatorRecord, IndicatorResult
from urbancode.provenance import (
    ProvenanceRecord,
    coverage_fraction,
    is_missing,
    quality_flags,
)
from urbancode.units import AnalysisUnits

_VALUE_STATS = {"mean", "min", "max", "median", "p50", "sum", "count", "weighted_mean"}
_GEOMETRY_STATS = {
    "coverage",
    "area_fraction",
    "length_density",
    "presence",
    "nearest_distance",
}


def aggregate(
    source: Layer | Any,
    units: AnalysisUnits,
    stat: str = "mean",
    *,
    indicator: str | None = None,
    column: str | None = None,
    weight: str | None = None,
    part: str = "nodes",
) -> IndicatorResult:
    """Summarize native spatial data on a shared unit frame.

    Raster pixels, graph nodes or edges, vector geometry, points, and
    georeferenced tables all produce the same long-form result contract.
    Missing cells stay null rather than being silently converted to zero.

    Args:
        source: A :class:`~urbancode.city.Layer` or compatible spatial
            object. Its native support is preserved until this call.
        units: Target polygons and stable unit IDs.
        stat: Summary name. Value summaries are ``mean``, ``min``, ``max``,
            ``median``/``p50``, ``sum``, ``count``, and ``weighted_mean``.
            Geometry summaries are ``coverage``, ``area_fraction``,
            ``length_density``, ``presence``, and ``nearest_distance``.
        indicator: Name written to every output record. Defaults to the
            source layer name where possible.
        column: Attribute to summarize for vector or graph inputs.
        weight: Weight column used by ``weighted_mean``.
        part: ``"nodes"`` or ``"edges"`` for graph inputs.

    Returns:
        An :class:`~urbancode.indicators.IndicatorResult` with one record per
        unit, including ``value``, ``coverage``, method parameters, and
        provenance. Read ``value`` together with ``coverage``.

    Raises:
        ValueError: If ``stat`` is unknown or required data are invalid.
        TypeError: If ``source`` has no supported spatial representation.
    """
    if stat not in _VALUE_STATS | _GEOMETRY_STATS:
        raise ValueError(f"unknown stat {stat!r}")
    if isinstance(source, Layer) and source.lazy and source.data is None:
        from urbancode.city import _materialize_layer

        source = _materialize_layer(source)
    layer = source if isinstance(source, Layer) else None
    kind = layer.kind if layer is not None else None
    if kind == "raster" or (layer is None and hasattr(source, "rio")):
        return _aggregate_raster(source, units, stat, indicator=indicator)
    if kind == "graph":
        return _aggregate_graph(
            layer, units, stat, indicator=indicator, column=column, part=part
        )
    frame = _as_frame(source)
    if frame is not None:
        return _aggregate_vector(
            source,
            frame,
            units,
            stat,
            indicator=indicator,
            column=column,
            weight=weight,
        )
    raise TypeError(
        "fusion.aggregate supports raster, graph, vector, point, or "
        f"georeferenced table Layers; got {kind or type(source).__name__}"
    )


def _as_frame(source: Any) -> Any | None:
    layer = source if isinstance(source, Layer) else None
    data = layer.data if layer is not None else source
    if data is not None and hasattr(data, "geometry"):
        return data
    if layer is not None and layer.kind == "table" and data is not None:
        return _table_to_points(data)
    if hasattr(data, "columns") and _lon_lat_columns(data)[0]:
        return _table_to_points(data)
    return None


def _lon_lat_columns(frame: Any) -> tuple[str | None, str | None]:
    cols = {str(c).lower(): str(c) for c in getattr(frame, "columns", [])}
    lon = cols.get("lon") or cols.get("longitude") or cols.get("lng") or cols.get("x")
    lat = cols.get("lat") or cols.get("latitude") or cols.get("y")
    return lon, lat


def _table_to_points(frame: Any) -> Any:
    gpd = require_extra("geopandas", "vector")
    lon, lat = _lon_lat_columns(frame)
    if not lon or not lat:
        raise TypeError("table aggregate needs lon/lat (or x/y) columns")
    return gpd.GeoDataFrame(
        frame.copy(),
        geometry=gpd.points_from_xy(frame[lon], frame[lat]),
        crs="EPSG:4326",
    )


def _aggregate_raster(
    source: Any,
    units: AnalysisUnits,
    stat: str,
    *,
    indicator: str | None,
) -> IndicatorResult:
    from urbancode.imagery.zonal import zonal_stats

    name = indicator or (source.name if isinstance(source, Layer) else "raster")
    zonal_stat = "mean" if stat in _GEOMETRY_STATS else stat
    if zonal_stat == "weighted_mean":
        zonal_stat = "mean"
    zonal = zonal_stats(source, units.frame, metrics=(zonal_stat, "coverage"))
    frame = zonal.data if isinstance(zonal, Layer) else zonal
    records = []
    for row in frame.itertuples(index=False):
        unit_id = str(getattr(row, "unit_id"))
        value = getattr(row, zonal_stat)
        cov_raw = getattr(row, "coverage", float("nan"))
        if is_missing(value):
            numeric = None
        else:
            numeric = float(value)
        cov = None if is_missing(cov_raw) else float(cov_raw)
        extra_flags = []
        if cov == 0.0 or (numeric is None and cov is None):
            extra_flags.append("nodata")
        if stat == "presence":
            numeric = 1.0 if numeric is not None else 0.0
        records.append(
            IndicatorRecord(
                city_id=units.city_id,
                unit_id=unit_id,
                indicator=name,
                value=numeric,
                unit=None
                if not isinstance(source, Layer)
                else (source.metadata or {}).get("unit"),
                method="zonal_stats",
                parameters={"stat": stat},
                source=source.source if isinstance(source, Layer) else None,
                coverage=cov,
                quality_flags=quality_flags(
                    value=numeric, coverage=cov, extra=extra_flags
                ),
                provenance_id=(
                    (source.metadata or {}).get("provenance_id")
                    if isinstance(source, Layer)
                    else None
                ),
            )
        )
    return _indicator_result(
        records,
        units,
        source if isinstance(source, Layer) else None,
        {"op": "aggregate", "kind": "raster", "stat": stat},
    )


def _graph_crs(layer: Layer) -> str:
    graph = layer.data
    graph_meta = getattr(graph, "graph", None) or {}
    return (
        layer.crs
        or graph_meta.get("crs")
        or (layer.metadata or {}).get("crs")
        or "EPSG:4326"
    )


def _aggregate_graph(
    layer: Layer,
    units: AnalysisUnits,
    stat: str,
    *,
    indicator: str | None,
    column: str | None,
    part: str,
) -> IndicatorResult:
    gpd = require_extra("geopandas", "vector")
    require_extra("networkx", "network")
    graph = layer.data
    if graph is None:
        raise ValueError(f"graph layer {layer.name!r} has no data")
    attr = column or (layer.metadata or {}).get("column")
    name = indicator or str(attr or part)
    rows = []
    if part == "edges":
        for u, v, data in graph.edges(data=True):
            try:
                x0, y0 = float(graph.nodes[u]["x"]), float(graph.nodes[u]["y"])
                x1, y1 = float(graph.nodes[v]["x"]), float(graph.nodes[v]["y"])
            except (KeyError, TypeError, ValueError):
                continue
            raw = data.get(attr) if attr else data.get("length")
            value = np.nan if is_missing(raw) else float(raw)
            rows.append({"x": (x0 + x1) / 2.0, "y": (y0 + y1) / 2.0, "value": value})
    else:
        if not attr and stat in _VALUE_STATS:
            raise ValueError("graph aggregate needs column= or layer.metadata['column']")
        for _node, data in graph.nodes(data=True):
            try:
                x, y = float(data["x"]), float(data["y"])
            except (KeyError, TypeError, ValueError):
                continue
            raw = data.get(attr) if attr else np.nan
            value = np.nan if is_missing(raw) else float(raw)
            rows.append({"x": x, "y": y, "value": value})
    if not rows:
        return _empty_graph_result(layer, units, name, stat, attr)
    points = gpd.GeoDataFrame(
        rows,
        geometry=gpd.points_from_xy([r["x"] for r in rows], [r["y"] for r in rows]),
        crs=_graph_crs(layer),
    )
    return _points_to_result(
        points,
        units,
        stat,
        name=name,
        source=layer,
        empty_flag="no_network",
        method="point_in_polygon",
        parameters={"stat": stat, "column": attr, "part": part},
    )


def _empty_graph_result(
    layer: Layer, units: AnalysisUnits, name: str, stat: str, attr: str | None
) -> IndicatorResult:
    records = [
        IndicatorRecord(
            city_id=units.city_id,
            unit_id=uid,
            indicator=name,
            value=None,
            method="point_in_polygon",
            parameters={"stat": stat, "column": attr},
            source=layer.source,
            coverage=0.0,
            quality_flags=quality_flags(
                value=None, coverage=0.0, extra=["no_network"]
            ),
        )
        for uid in units.unit_ids
    ]
    return _indicator_result(
        records, units, layer, {"op": "aggregate", "kind": "graph", "stat": stat}
    )


def _aggregate_vector(
    source: Any,
    frame: Any,
    units: AnalysisUnits,
    stat: str,
    *,
    indicator: str | None,
    column: str | None,
    weight: str | None,
) -> IndicatorResult:
    gpd = require_extra("geopandas", "vector")
    layer = source if isinstance(source, Layer) else None
    name = indicator or (layer.name if layer is not None else "vector")
    geom_types = set(getattr(frame.geometry, "geom_type", []))
    points = frame
    if points.crs is not None and units.frame.crs is not None:
        if str(points.crs) != str(units.frame.crs):
            points = points.to_crs(units.frame.crs)
    if stat == "nearest_distance":
        return _nearest_distance(points, units, name, layer)
    if geom_types <= {"Point", "MultiPoint"} or all(
        getattr(g, "geom_type", "") in {"Point", "MultiPoint"} for g in points.geometry
    ):
        value_col = column or (layer.metadata or {}).get("column") if layer else column
        work = points.copy()
        if value_col:
            if value_col not in work.columns:
                raise KeyError(
                    f"aggregate column {value_col!r} is missing; "
                    f"have {sorted(map(str, work.columns))}"
                )
            work["value"] = work[value_col]
        else:
            work["value"] = 1.0
        if weight and weight in work.columns:
            work["weight"] = work[weight]
        return _points_to_result(
            work,
            units,
            stat,
            name=name,
            source=layer,
            empty_flag="no_observation",
            method="point_in_polygon",
            parameters={"stat": stat, "column": value_col},
        )
    return _polygon_or_line(
        gpd, points, units, stat, name=name, layer=layer, column=column
    )


def _polygon_or_line(
    gpd: Any,
    frame: Any,
    units: AnalysisUnits,
    stat: str,
    *,
    name: str,
    layer: Layer | None,
    column: str | None,
) -> IndicatorResult:
    zones = units.frame[["unit_id", units.frame.geometry.name]].copy()
    zones["_area"] = zones.geometry.area
    overlay = gpd.overlay(frame, zones, how="intersection", keep_geom_type=False)
    records = []
    by_id = {str(k): g for k, g in overlay.groupby("unit_id")} if not overlay.empty else {}
    zone_areas = {
        str(uid): float(area) or 1.0
        for uid, area in zip(zones["unit_id"], zones["_area"])
    }
    for unit_id in units.unit_ids:
        grp = by_id.get(unit_id)
        extra = []
        if grp is None or grp.empty:
            extra.append("no_observation")
            numeric = 0.0 if stat in {"presence", "area_fraction", "length_density", "count"} else None
            cov = 0.0
        else:
            inter_area = float(grp.geometry.area.sum())
            zone_area = zone_areas.get(unit_id) or 1.0
            if stat == "area_fraction":
                numeric = inter_area / zone_area
            elif stat == "length_density":
                numeric = float(grp.geometry.length.sum()) / zone_area
            elif stat == "presence":
                numeric = 1.0
            elif stat == "count":
                numeric = float(len(grp))
            elif column:
                if column not in grp.columns:
                    raise KeyError(
                        f"aggregate column {column!r} is missing; "
                        f"have {sorted(map(str, grp.columns))}"
                    )
                values = np.asarray(grp[column], dtype=float)
                values = values[np.isfinite(values)]
                numeric = float(_stat(values, stat)) if values.size else None
            else:
                numeric = inter_area / zone_area
            cov = min(1.0, inter_area / zone_area)
        records.append(
            IndicatorRecord(
                city_id=units.city_id,
                unit_id=unit_id,
                indicator=name,
                value=numeric,
                method="overlay",
                parameters={"stat": stat, "column": column},
                source=layer.source if layer is not None else None,
                coverage=cov,
                quality_flags=quality_flags(value=numeric, coverage=cov, extra=extra),
                provenance_id=(layer.metadata or {}).get("provenance_id")
                if layer is not None
                else None,
            )
        )
    return _indicator_result(
        records, units, layer, {"op": "aggregate", "kind": "vector", "stat": stat}
    )


def _nearest_distance(
    frame: Any, units: AnalysisUnits, name: str, layer: Layer | None
) -> IndicatorResult:
    records = []
    for unit_id, geom in zip(units.unit_ids, units.frame.geometry):
        centroid = geom.centroid
        dist = float(frame.distance(centroid).min()) if len(frame) else None
        records.append(
            IndicatorRecord(
                city_id=units.city_id,
                unit_id=unit_id,
                indicator=name,
                value=dist,
                unit="metre",
                method="nearest_distance",
                coverage=1.0 if dist is not None else 0.0,
                quality_flags=quality_flags(
                    value=dist,
                    coverage=1.0 if dist is not None else 0.0,
                    extra=[] if dist is not None else ["no_observation"],
                ),
                provenance_id=(layer.metadata or {}).get("provenance_id")
                if layer is not None
                else None,
            )
        )
    return _indicator_result(
        records,
        units,
        layer,
        {"op": "aggregate", "kind": "vector", "stat": "nearest_distance"},
    )


def _points_to_result(
    points: Any,
    units: AnalysisUnits,
    stat: str,
    *,
    name: str,
    source: Layer | None,
    empty_flag: str,
    method: str,
    parameters: dict[str, Any],
) -> IndicatorResult:
    gpd = require_extra("geopandas", "vector")
    zones = units.frame
    if points.crs is not None and zones.crs is not None:
        if str(points.crs) != str(zones.crs):
            points = points.to_crs(zones.crs)
    geom_col = zones.geometry.name
    zone_view = zones[["unit_id", geom_col]]
    joined = gpd.sjoin(points, zone_view, predicate="within", how="left")
    missing = joined["unit_id"].isna()
    if missing.any():
        leftover = points.loc[points.index.intersection(joined.index[missing])].copy()
        if leftover.empty:
            leftover = points.iloc[missing.to_numpy()].copy()
        hit = gpd.sjoin(leftover, zone_view, predicate="intersects", how="left")
        if not hit.empty:
            hit = hit.sort_values("unit_id", kind="stable")
            hit = hit[~hit.index.duplicated(keep="first")]
            joined.loc[hit.index, "unit_id"] = hit["unit_id"]
    grouped = joined.groupby("unit_id", dropna=False)
    by_id = {str(key): grp for key, grp in grouped if not is_missing(key)}
    records = []
    for unit_id in units.unit_ids:
        grp = by_id.get(unit_id)
        extra_flags = []
        if source is not None and (source.metadata or {}).get("location_quality") == "illustrative":
            extra_flags.append("synthetic_location")
        if grp is None or grp.empty:
            extra_flags.append(empty_flag)
            values = np.asarray([], dtype=float)
        else:
            values = np.asarray(grp.get("value", [1.0] * len(grp)), dtype=float)
            values = values[np.isfinite(values)]
        if stat == "presence":
            numeric = 1.0 if values.size else 0.0
            cov = 1.0 if values.size else 0.0
        elif stat == "count":
            numeric = float(values.size)
            cov = 1.0 if values.size else 0.0
        elif values.size == 0:
            numeric = None
            cov = 0.0
        elif stat == "weighted_mean" and "weight" in getattr(grp, "columns", []):
            weights = np.asarray(grp["weight"], dtype=float)
            mask = np.isfinite(weights) & np.isfinite(np.asarray(grp["value"], dtype=float))
            if not mask.any():
                numeric = None
                cov = 0.0
            else:
                numeric = float(
                    np.average(np.asarray(grp["value"], dtype=float)[mask], weights=weights[mask])
                )
                cov = coverage_fraction(int(mask.sum()), max(int(len(grp)), 1))
        else:
            numeric = float(_stat(values, stat if stat != "coverage" else "count"))
            if stat == "coverage":
                numeric = coverage_fraction(int(values.size), max(int(len(grp)), 1))
            cov = coverage_fraction(int(values.size), max(int(len(grp)), 1))
        records.append(
            IndicatorRecord(
                city_id=units.city_id,
                unit_id=unit_id,
                indicator=name,
                value=numeric,
                unit=(source.metadata or {}).get("unit") if source is not None else None,
                method=method,
                parameters=parameters,
                source=source.source if source is not None else None,
                coverage=cov,
                quality_flags=quality_flags(
                    value=numeric, coverage=cov, extra=extra_flags
                ),
                provenance_id=(source.metadata or {}).get("provenance_id")
                if source is not None
                else None,
            )
        )
    return _indicator_result(
        records, units, source, {"op": "aggregate", "kind": "vector", "stat": stat}
    )


def aggregate_many(
    source: Layer | Any,
    units: AnalysisUnits,
    columns: dict[str, dict[str, Any] | str],
    stat: str = "mean",
) -> IndicatorResult:
    """Aggregate several attributes from one source onto the same units.

    Args:
        source: Spatial layer or compatible object containing every requested
            source column.
        units: Shared target polygons.
        columns: Mapping from source column to an indicator name, or to a
            mapping with ``indicator`` and optional ``unit`` keys.
        stat: Summary applied independently to every requested column.

    Returns:
        One long :class:`~urbancode.indicators.IndicatorResult` containing all
        requested indicators. Units with no observations remain null.

    Raises:
        ValueError: If ``columns`` is empty or the selected statistic fails.

    Notes:
        This is a convenience wrapper around :func:`aggregate` followed by
        :func:`combine`; it does not calculate relationships between columns.
    """
    if not columns:
        raise ValueError("aggregate_many needs a non-empty columns mapping")
    parts: list[IndicatorResult] = []
    for column, spec in columns.items():
        if isinstance(spec, str):
            indicator = spec
            unit = None
        else:
            indicator = spec.get("indicator") or column
            unit = spec.get("unit")
        part = aggregate(
            source,
            units,
            stat=stat,
            indicator=indicator,
            column=column,
        )
        if unit:
            for record in part.records:
                if record.unit is None:
                    record.unit = unit
            part.metadata = dict(part.metadata or {})
            part.metadata["unit"] = unit
        parts.append(part)
    result = combine(units, *parts)
    result.metadata = dict(result.metadata or {})
    result.metadata["op"] = "aggregate_many"
    result.metadata["stat"] = stat
    result.metadata["columns"] = {
        column: (spec if isinstance(spec, dict) else {"indicator": spec})
        for column, spec in columns.items()
    }
    return result


def combine(units: AnalysisUnits, *results: IndicatorResult) -> IndicatorResult:
    """Concatenate results that already share one unit frame.

    Args:
        units: Authoritative target units for the combined result.
        *results: Indicator results created on those units.

    Returns:
        A long :class:`~urbancode.indicators.IndicatorResult` containing every
        input record and a combined provenance receipt.

    Raises:
        ValueError: If city ID, CRS, unit scheme, resolution, or unit IDs do
            not match.

    Notes:
        ``combine`` does no spatial work and computes no composite score. Use
        :func:`aggregate` first when a source is still on pixels, nodes, or
        vector geometry.
    """
    expected = _units_signature(units)
    for result in results:
        if result.units is None:
            cities = {r.city_id for r in result.records}
            if cities and cities != {units.city_id}:
                raise ValueError(
                    f"combine city_id mismatch: {cities} vs {units.city_id!r}"
                )
            ids = {r.unit_id for r in result.records}
            if ids and not ids <= set(units.unit_ids):
                raise ValueError("combine unit_id set does not match AnalysisUnits")
            continue
        got = _units_signature(result.units)
        for key in ("city_id", "crs", "scheme", "resolution"):
            if got[key] and expected[key] and got[key] != expected[key]:
                raise ValueError(
                    f"combine {key} mismatch: {got[key]!r} vs {expected[key]!r}"
                )
        if set(result.units.unit_ids) != set(units.unit_ids):
            raise ValueError("combine unit_id set does not match AnalysisUnits")
    records = []
    receipts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for result in results:
        records.extend(result.records)
        for item in result.metadata.get("provenance") or []:
            key = str(item.get("provenance_id") or item)
            if key in seen:
                continue
            seen.add(key)
            receipts.append(item)
    combine_receipt = ProvenanceRecord(
        method="combine",
        parameters={"n_inputs": len(results)},
        parent_layer_ids=[
            str(item.get("provenance_id"))
            for item in receipts
            if item.get("provenance_id")
        ],
    ).to_record()
    receipts.append(combine_receipt)
    return IndicatorResult(
        records=records,
        units=units,
        metadata={
            "op": "combine",
            "n_inputs": len(results),
            "provenance": receipts,
        },
    )


def _layer_receipts(layer: Layer | None) -> list[dict[str, Any]]:
    if layer is None:
        return []
    meta = layer.metadata or {}
    raw = meta.get("provenance")
    if isinstance(raw, list):
        return [dict(item) for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        return [dict(raw)]
    return []


def _indicator_result(
    records: list[IndicatorRecord],
    units: AnalysisUnits,
    layer: Layer | None,
    metadata: dict[str, Any],
) -> IndicatorResult:
    receipts = _layer_receipts(layer)
    agg = ProvenanceRecord(
        method="aggregate",
        parameters=dict(metadata),
        parent_layer_ids=[
            str(item.get("provenance_id"))
            for item in receipts
            if item.get("provenance_id")
        ],
        source=layer.source if layer is not None else None,
        crs=str(units.crs or units.metric_crs or ""),
    ).to_record()
    receipts.append(agg)
    meta = dict(metadata)
    meta["provenance"] = receipts
    return IndicatorResult(records=records, units=units, metadata=meta)


def _units_signature(units: AnalysisUnits) -> dict[str, Any]:
    return {
        "city_id": units.city_id,
        "crs": str(units.crs or units.metric_crs or ""),
        "scheme": (units.metadata or {}).get("scheme"),
        "resolution": units.cell_size,
    }


def _stat(values: np.ndarray, name: str) -> float:
    if name == "mean":
        return float(np.mean(values))
    if name == "min":
        return float(np.min(values))
    if name == "max":
        return float(np.max(values))
    if name == "median" or name == "p50":
        return float(np.median(values))
    if name == "sum":
        return float(np.sum(values))
    if name == "count":
        return float(values.size)
    raise ValueError(f"unknown stat {name!r}")
