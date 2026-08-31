"""Layer-returning perception predictors. Torch loads only on call."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from urbancode.city import Layer
from urbancode.errors import require_extra
from urbancode.perception.backends.tcis import (
    CANONICAL_SCORE,
    LEGACY_SCORE,
    SCORE_UNIT,
    predict_paths,
)
from urbancode.perception.backends.tcis_runtime import run_dataset
from urbancode.provenance import stamp_layer


def thermal_affordance(
    images: Layer | Any,
    *,
    device: str = "cpu",
        include_features: bool = True,
    batch_size: int = 1,
    workers: int = 0,
    chunk_size: int | None = None,
    resume: bool = False,
    output: str | Path | None = None,
    image_root: str | Path | None = None,
    run_id: str | None = None,
) -> Layer:
    """Predict TCIS visual thermal affordance (VATA) and VPI heads.

    ``thermal_affordance`` is VATA: a model score of visual/spatial
    thermal affordance. It is not measured personal thermal comfort
    and it is not UTCI.

    Small catalogs and 92k-image runs share this entry. Pass
    ``output``, ``chunk_size``, and ``resume=True`` for dataset-scale
    GPU jobs. Models load once per call.

    Args:
        images: An image-observation Layer from ``uc.images.from_table``,
            a table with ``image_path`` / ``Filename``, a folder, or a
            single image path.
        device: ``cpu`` or ``cuda``.
        include_features: Keep TCIS initial-feature (IF) columns. Default True.
        batch_size: GPU batch size for IF extractors and TCIS.
        workers: Reserved for image-loading workers (0 = in-process).
        chunk_size: Rows written per atomic parquet chunk.
        resume: Skip ``image_id`` values already in ``output``.
        output: Optional parquet path. Absolute image paths are not written.
        image_root: Resolve ``relative_path`` against this directory.
        run_id: Optional stable run identifier.

    Returns:
        Point vector Layer when coordinates exist, otherwise a table Layer.
    """
    if isinstance(images, (str, Path)):
        path = Path(images)
        if path.is_dir():
            files = sorted(
                p
                for p in path.iterdir()
                if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
            )
            predicted = predict_paths(
                [str(p) for p in files],
                device=device,
                include_features=include_features,
            )
            return _predictions_to_layer(predicted, None, device=device)
        if path.is_file():
            predicted = predict_paths(
                [str(path)], device=device, include_features=include_features
            )
            return _predictions_to_layer(predicted, None, device=device)
        raise FileNotFoundError(str(path))

    frame, source_layer = _as_image_frame(images)
    if (
        "image_path" not in frame.columns
        and "Filename" not in frame.columns
        and "relative_path" not in frame.columns
    ):
        raise TypeError(
            "thermal_affordance needs an images Layer, a table with "
            "image_path/Filename/relative_path, a folder, or an image path"
        )
    predicted = run_dataset(
        frame,
        device=device,
        include_features=include_features,
        batch_size=batch_size,
        workers=workers,
        chunk_size=chunk_size,
        resume=resume,
        output=output,
        image_root=image_root or _folder_from_frame(frame),
        run_id=run_id,
    )
    return _predictions_to_layer(predicted, source_layer, device=device)


def _as_image_frame(images: Any) -> tuple[Any, Layer | None]:
    if isinstance(images, Layer):
        data = images.data
        if data is None:
            raise ValueError(f"layer {images.name!r} has no data")
        return data.copy(), images
    if images is None:
        raise TypeError("thermal_affordance needs images")
    return images.copy(), None


def _folder_from_frame(frame: Any) -> str | None:
    if "image_path" in frame.columns and len(frame):
        first = Path(str(frame["image_path"].iloc[0]))
        if first.is_file() or first.parent.is_dir():
            return str(first.parent)
    return None


def _predictions_to_layer(
    frame: Any,
    source_layer: Layer | None,
    *,
    device: str,
) -> Layer:
    provenance = dict(getattr(frame, "attrs", {}).get("tcis_provenance") or {})
    has_geom = hasattr(frame, "geometry") and getattr(frame, "geometry", None) is not None
    lon_lat = _lon_lat_columns(frame)
    if has_geom:
        data = frame
        kind = "vector"
        crs = getattr(frame, "crs", None) or (
            source_layer.crs if source_layer is not None else "EPSG:4326"
        )
    elif lon_lat[0] and lon_lat[1]:
        gpd = require_extra("geopandas", "vector")
        data = gpd.GeoDataFrame(
            frame,
            geometry=gpd.points_from_xy(frame[lon_lat[0]], frame[lon_lat[1]]),
            crs="EPSG:4326",
        )
        kind = "vector"
        crs = "EPSG:4326"
    else:
        data = frame
        kind = "table"
        crs = None

    parent = []
    if source_layer is not None:
        parent.append((source_layer.metadata or {}).get("provenance_id"))
    layer = Layer(
        name=CANONICAL_SCORE,
        kind=kind,
        data=data,
        crs=crs,
        source="urbancode.perception.thermal_affordance",
        metadata={
            "processing": {
                "op": "thermal_affordance",
                "backend": "tcis",
                "device": device,
            },
            "column": CANONICAL_SCORE,
            "unit": SCORE_UNIT,
            "legacy_alias": {LEGACY_SCORE: CANONICAL_SCORE},
            "model": provenance,
            "parent_layer_ids": [item for item in parent if item],
        },
    )
    stamp_layer(
        layer,
        method="thermal_affordance",
        assumptions=[
            "VATA is visual thermal affordance, not measured comfort and not UTCI",
            f"training geography: {provenance.get('training_geography')}",
        ],
    )
    return layer


def _lon_lat_columns(frame: Any) -> tuple[str | None, str | None]:
    cols = {str(c).lower(): str(c) for c in getattr(frame, "columns", [])}
    lon = cols.get("lon") or cols.get("longitude") or cols.get("lng") or cols.get("x")
    lat = cols.get("lat") or cols.get("latitude") or cols.get("y")
    return lon, lat
