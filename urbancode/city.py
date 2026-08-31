"""City container: named layers with a stable on-disk contract."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Literal, Mapping

from urbancode._version import __version__ as PACKAGE_VERSION
from urbancode.errors import CityIntegrityError

LayerKind = Literal["vector", "raster", "table", "graph", "images"]
DEFAULT_VECTOR_CRS = "EPSG:4326"
SCHEMA_VERSION = 1
SAFE_LAYER_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
_ABS_DRIVE = re.compile(r"^[A-Za-z]:")


def _json_safe(value: Any) -> Any:
    """Replace NaN/Inf with None so manifests stay standard JSON."""
    if isinstance(value, float):
        if value != value or value in {float("inf"), float("-inf")}:
            return None
        return value
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _require_geopandas():
    from urbancode.errors import require_extra

    return require_extra("geopandas", "vector")


def validate_layer_name(name: str) -> str:
    if not name or not SAFE_LAYER_NAME.match(name) or ".." in name:
        raise ValueError(
            f"unsafe layer name {name!r}; use letters, digits, '.', '_' or '-'"
        )
    return name


def _safe_city_path(root: Path, rel: str | None) -> Path:
    """Resolve ``rel`` and require it to stay inside ``root``.

    Rejects empty values, absolute paths, and ``..`` escapes.
    """
    if rel is None or not str(rel).strip():
        raise CityIntegrityError("manifest path is empty")
    raw = str(rel).strip()
    as_path = Path(raw)
    if as_path.is_absolute() or raw.startswith(("/", "\\")) or _ABS_DRIVE.match(raw):
        raise CityIntegrityError(f"absolute path not allowed: {rel!r}")
    root_res = Path(root).resolve()
    candidate = (root_res / raw).resolve()
    try:
        candidate.relative_to(root_res)
    except ValueError as exc:
        raise CityIntegrityError(f"path escapes city root: {rel!r}") from exc
    return candidate


@dataclass
class Layer:
    """One named urban data layer plus provenance."""

    name: str
    kind: LayerKind
    data: Any = None
    path: str | None = None
    crs: Any | None = None
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    lazy: bool = False

    def to_record(self) -> dict[str, Any]:
        """JSON-serializable metadata (no in-memory payload)."""
        record = {
            "name": self.name,
            "kind": self.kind,
            "path": self.path,
            "crs": _crs_to_str(self.crs),
            "source": self.source,
            "metadata": self.metadata,
        }
        record.update(_raster_grid_fields(self))
        return record

    def materialize(self) -> "Layer":
        """Load a deferred payload in place.

        Rasters require ``urbancode[imagery]``. Missing extras raise
        :class:`~urbancode.errors.MissingExtraError` instead of leaving
        a path string in ``data``.
        """
        return _materialize_layer(self)

    def plot(
        self,
        title: str | None = None,
        overlay: Any = None,
        column: str | None = None,
        save: str | Path | None = None,
        ax: Any = None,
        context: Any = None,
        **style: Any,
    ) -> Path | Any:
        """Draw this layer. Pass ``save=`` to write a PNG without importing matplotlib."""
        from urbancode.plot import plot_layer

        if context is not None:
            style.setdefault("context", context)
        return plot_layer(
            self, title=title, overlay=overlay, column=column, save=save, ax=ax, **style
        )

    def save(self, path: str | Path) -> Path:
        """Write this layer to ``path`` (GeoPackage, GeoTIFF, GraphML, CSV, or image)."""
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if self.kind == "vector":
            if self.data is None:
                raise ValueError(f"layer {self.name!r} has no data to save")
            if dest.suffix.lower() == ".csv":
                frame = self.data.drop(columns="geometry", errors="ignore")
                frame.to_csv(dest, index=False)
                return dest
            driver = "GPKG" if dest.suffix.lower() in {".gpkg", ""} else None
            self.data.to_file(dest, driver=driver)
            return dest
        if self.kind == "table":
            if self.data is None:
                raise ValueError(f"layer {self.name!r} has no data to save")
            if dest.suffix.lower() == ".parquet":
                self.data.to_parquet(dest, index=False)
            else:
                self.data.to_csv(dest, index=False)
            return dest
        if self.kind == "raster":
            return _save_raster_layer(self, dest)
        if self.kind == "graph":
            if self.data is None:
                raise ValueError(f"layer {self.name!r} has no data to save")
            _write_graphml(self.data, dest)
            return dest
        if self.kind == "images":
            src = self.path
            if src and Path(src).exists():
                if Path(src).resolve() != dest.resolve():
                    shutil.copy2(src, dest)
                return dest
            raise ValueError(f"image layer {self.name!r} has no file to save")
        raise ValueError(f"cannot save layer kind {self.kind!r}")


@dataclass
class City:
    """A place plus named layers.

    ``city["streets"]`` returns the layer payload.
    ``city.layer("streets")`` returns the :class:`Layer` (with metadata).
    """

    place: str | None = None
    boundary: Any = None
    layers: dict[str, Layer] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    study_area: Any = None

    def __post_init__(self) -> None:
        from urbancode.area import StudyArea

        if isinstance(self.place, StudyArea):
            area = self.place
            object.__setattr__(self, "study_area", area)
            object.__setattr__(self, "place", area.place)
        elif self.study_area is not None and self.place is None:
            object.__setattr__(self, "place", getattr(self.study_area, "place", None))

    def keys(self) -> list[str]:
        return list(self.layers.keys())

    def __contains__(self, name: str) -> bool:
        return name in self.layers

    def __getitem__(self, name: str) -> Any:
        return self.layer(name).data

    def __iter__(self) -> Iterator[str]:
        return iter(self.layers)

    def layer(self, name: str) -> Layer:
        if name not in self.layers:
            raise KeyError(f"unknown layer {name!r}; have {self.keys()}")
        return self.layers[name].materialize()

    def add_layer(
        self,
        name: str,
        data: Any = None,
        *,
        kind: LayerKind,
        path: str | None = None,
        crs: Any | None = None,
        source: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        overwrite: bool = False,
        lazy: bool = False,
    ) -> Layer:
        """Add a layer. Name collisions raise unless ``overwrite=True``."""
        validate_layer_name(name)
        if name in self.layers and not overwrite:
            raise ValueError(
                f"layer {name!r} already exists; pass overwrite=True to replace"
            )
        layer = Layer(
            name=name,
            kind=kind,
            data=data,
            path=path,
            crs=crs,
            source=source,
            metadata=dict(metadata or {}),
            lazy=lazy,
        )
        self.layers[name] = layer
        return layer

    def record_error(self, name: str, message: str, **extra: Any) -> None:
        entry = {"layer": name, "message": message, **extra}
        self.errors.append(entry)

    def describe(self) -> dict[str, Any]:
        """Layer inventory. Does not materialize lazy payloads."""
        area = self.study_area
        return {
            "place": self.place,
            "study_area": None
            if area is None
            else {
                "bbox": getattr(area, "bbox", None),
                "geographic_crs": getattr(area, "geographic_crs", None),
                "metric_crs": getattr(area, "metric_crs", None),
            },
            "layers": [
                {
                    "name": name,
                    "kind": layer.kind,
                    "crs": _crs_to_str(layer.crs),
                    "loaded": layer.data is not None,
                    "lazy": layer.lazy,
                }
                for name, layer in self.layers.items()
            ],
            "errors": len(self.errors),
        }

    def validate(self) -> list[str]:
        """Return human-readable issues. Empty means the City looks usable."""
        issues: list[str] = []
        schema = self.metadata.get("schema_version")
        if schema not in (None, SCHEMA_VERSION, 1):
            issues.append(
                f"unsupported schema_version {schema!r}; expected {SCHEMA_VERSION}"
            )
        for name, layer in self.layers.items():
            try:
                validate_layer_name(name)
            except ValueError as exc:
                issues.append(str(exc))
            if layer.kind not in {"vector", "raster", "table", "graph", "images"}:
                issues.append(f"layer {name!r} has unknown kind {layer.kind!r}")
        return issues

    def quality_report(self) -> dict[str, Any]:
        """Errors, validation issues, and per-layer quality flags."""
        layers = []
        for name, layer in self.layers.items():
            flags = list((layer.metadata or {}).get("quality_flags") or [])
            coverage = (layer.metadata or {}).get("coverage")
            layers.append(
                {
                    "name": name,
                    "kind": layer.kind,
                    "coverage": coverage,
                    "quality_flags": flags,
                    "loaded": layer.data is not None,
                }
            )
        return {
            "place": self.place,
            "issues": self.validate(),
            "errors": list(self.errors),
            "layers": layers,
        }

    def save(self, directory: str | Path, *, overwrite: bool = True) -> Path:
        """Write this City to a directory. Alias of ``to_dir``."""
        return self.to_dir(directory, overwrite=overwrite)

    def plot(
        self,
        layers: list[str] | None = None,
        title: str | None = None,
        save: str | Path | None = None,
        basemap: bool = False,
        ax: Any = None,
        **style: Any,
    ) -> Path | Any:
        """Draw named layers. Pass ``save=`` to write a PNG without importing matplotlib."""
        from urbancode.plot import plot_city

        return plot_city(
            self, layers=layers, title=title, save=save, basemap=basemap, ax=ax, **style
        )

    def to_dir(self, directory: str | Path, *, overwrite: bool = True) -> Path:
        """Write ``manifest.json`` plus per-layer files."""
        out = Path(directory)
        manifest_path = out / "manifest.json"
        if manifest_path.exists() and not overwrite:
            raise FileExistsError(
                f"{manifest_path} already exists; pass overwrite=True to replace"
            )
        if manifest_path.exists() and overwrite:
            _remove_previous_artifacts(out)
        out.mkdir(parents=True, exist_ok=True)
        layer_dir = out / "layers"
        layer_dir.mkdir(exist_ok=True)

        records: list[dict[str, Any]] = []
        for name, layer in self.layers.items():
            validate_layer_name(name)
            rel = _write_layer(layer, layer_dir)
            record = layer.to_record()
            record["path"] = rel
            if rel and not (layer.kind == "images" and layer.metadata.get("external")):
                abs_path = _safe_city_path(out, rel)
                if abs_path.exists() and layer.kind == "raster":
                    record["checksum"] = _sha256(abs_path)
                    record.update(_raster_file_fields(abs_path))
            records.append(record)

        if self.layers and not any(r.get("path") for r in records):
            raise CityIntegrityError(
                "refusing to write a layer-less manifest; every layer is "
                "missing data and a source file"
            )

        boundary_rel = None
        if self.boundary is not None:
            boundary_rel = "boundary.gpkg"
            gpd = _require_geopandas()
            gdf = self.boundary
            if not hasattr(gdf, "to_file"):
                raise TypeError("City.boundary must be a GeoDataFrame")
            gdf.to_file(out / boundary_rel, driver="GPKG")

        study_area_record = None
        if self.study_area is not None and hasattr(self.study_area, "to_record"):
            study_area_record = self.study_area.to_record()
            bound = getattr(self.study_area, "boundary", None)
            geom = (
                bound
                if bound is not None
                else getattr(self.study_area, "geometry", None)
            )
            if geom is None and getattr(self.study_area, "bbox", None) is not None:
                from shapely.geometry import box

                gpd = _require_geopandas()
                geom = gpd.GeoDataFrame(
                    geometry=[box(*self.study_area.bbox)],
                    crs=getattr(self.study_area, "geographic_crs", None)
                    or "EPSG:4326",
                )
            elif geom is not None and not hasattr(geom, "to_file"):
                gpd = _require_geopandas()
                crs = getattr(geom, "crs", None) or getattr(
                    self.study_area, "geographic_crs", None
                )
                geom = gpd.GeoDataFrame(geometry=[geom], crs=crs)
            if geom is not None and hasattr(geom, "to_file"):
                area_rel = "area/study_area.gpkg"
                (out / "area").mkdir(exist_ok=True)
                geom.to_file(out / area_rel, driver="GPKG")
                study_area_record["boundary"] = area_rel

        receipts = list(self.metadata.get("provenance") or [])
        if receipts:
            prov_dir = out / "provenance"
            prov_dir.mkdir(exist_ok=True)
            (prov_dir / "receipts.jsonl").write_text(
                "\n".join(json.dumps(item, default=str) for item in receipts) + "\n",
                encoding="utf-8",
            )

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "urbancode_version": PACKAGE_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "place": self.place,
            "boundary": boundary_rel,
            "study_area": study_area_record,
            "layers": records,
            "metadata": self.metadata,
            "errors": self.errors,
            "default_vector_crs": DEFAULT_VECTOR_CRS,
        }
        manifest_path.write_text(
            json.dumps(_json_safe(manifest), indent=2, default=str, allow_nan=False),
            encoding="utf-8",
        )
        return out

    @classmethod
    def from_dir(
        cls,
        directory: str | Path,
        *,
        verify: bool = False,
        layers: list[str] | None = None,
        lazy: bool = False,
    ) -> City:
        """Rehydrate a City written by ``to_dir``.

        ``verify=True`` checks ``schema_version`` and raster checksums.
        ``layers`` loads only those names. ``lazy=True`` defers file reads
        until ``city[name]`` / ``city.layer(name)``.
        """
        root = Path(directory)
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        schema = manifest.get("schema_version")
        if verify:
            if schema != SCHEMA_VERSION:
                raise CityIntegrityError(
                    f"unsupported schema_version {schema!r}; expected {SCHEMA_VERSION}"
                )
        city = cls(
            place=manifest.get("place"),
            metadata=dict(manifest.get("metadata") or {}),
            errors=list(manifest.get("errors") or []),
        )
        city.metadata.setdefault("schema_version", schema)
        city.metadata.setdefault("urbancode_version", manifest.get("urbancode_version"))
        area_record = manifest.get("study_area")
        if area_record:
            from urbancode.area import StudyArea

            city.study_area = StudyArea.from_record(area_record)
            bound = area_record.get("boundary")
            if bound and not lazy:
                gpd = _require_geopandas()
                city.study_area.boundary = gpd.read_file(_safe_city_path(root, bound))
        receipts_path = root / "provenance" / "receipts.jsonl"
        if receipts_path.exists() and "provenance" not in city.metadata:
            lines = []
            for line in receipts_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    lines.append(json.loads(line))
            city.metadata["provenance"] = lines
        wanted = set(layers) if layers is not None else None
        if wanted is not None:
            unknown = sorted(wanted - {r["name"] for r in (manifest.get("layers") or [])})
            if unknown:
                raise KeyError(f"unknown layer(s) {unknown}; not in manifest")
        boundary_rel = manifest.get("boundary")
        if boundary_rel and wanted is None and not lazy:
            gpd = _require_geopandas()
            city.boundary = gpd.read_file(_safe_city_path(root, boundary_rel))
        for record in manifest.get("layers") or []:
            if wanted is not None and record["name"] not in wanted:
                continue
            kind = record["kind"]
            meta = record.get("metadata") or {}
            if kind == "images" and meta.get("external"):
                city.add_layer(
                    record["name"],
                    None,
                    kind=kind,
                    path=record.get("path"),
                    crs=record.get("crs"),
                    source=record.get("source"),
                    metadata=meta,
                    overwrite=True,
                    lazy=lazy,
                )
                continue
            rel = record.get("path")
            abs_path = str(_safe_city_path(root, rel)) if rel else None
            if verify and kind == "raster":
                expected = record.get("checksum")
                if not expected:
                    raise CityIntegrityError(
                        f"layer {record.get('name')!r} is missing a checksum"
                    )
                if abs_path is None or not Path(abs_path).exists():
                    raise CityIntegrityError(
                        f"layer {record.get('name')!r} raster file is missing"
                    )
                actual = _sha256(Path(abs_path))
                if actual != expected:
                    raise CityIntegrityError(
                        f"layer {record.get('name')!r} checksum mismatch"
                    )
            data = None
            if not lazy and abs_path:
                data = _read_layer(kind, abs_path, record)
            city.add_layer(
                record["name"],
                data,
                kind=kind,
                path=abs_path,
                crs=record.get("crs"),
                source=record.get("source"),
                metadata=meta,
                overwrite=True,
                lazy=lazy,
            )
        return city

    def to_gpkg(self, path: str | Path) -> Path:
        """Write all vector layers into one GeoPackage."""
        gpd = _require_geopandas()
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            out.unlink()
        wrote = False
        for name, layer in self.layers.items():
            if layer.kind != "vector" or layer.data is None:
                continue
            layer.data.to_file(out, layer=name, driver="GPKG")
            wrote = True
        if self.boundary is not None:
            self.boundary.to_file(out, layer="boundary", driver="GPKG")
            wrote = True
        if not wrote:
            empty = gpd.GeoDataFrame(geometry=[], crs=DEFAULT_VECTOR_CRS)
            empty.to_file(out, layer="empty", driver="GPKG")
        return out


def load(
    directory: str | Path,
    *,
    layers: list[str] | None = None,
    lazy: bool = False,
    verify: bool = False,
) -> City:
    """Open a City directory written by ``City.save`` / ``City.to_dir``.

    ``layers`` selects names from the manifest. ``lazy=True`` does not
    read payloads (so a raster-only selection does not need GeoPandas).
    """
    return City.from_dir(directory, verify=verify, layers=layers, lazy=lazy)


def _save_raster_layer(layer: Layer, dest: Path) -> Path:
    from urbancode.imagery.write import write_geotiff

    data = layer.data
    if data is not None and hasattr(data, "rio"):
        data.rio.to_raster(dest)
        return dest
    array = None
    transform = (layer.metadata or {}).get("transform")
    if hasattr(data, "shape") and hasattr(data, "dtype") and not hasattr(data, "rio"):
        array = data
    elif data is None and layer.path and Path(layer.path).exists():
        shutil.copy2(layer.path, dest)
        return dest
    if array is None:
        raise ValueError(f"raster layer {layer.name!r} has no array or GeoTIFF to save")
    if transform is None:
        raise ValueError(
            f"raster layer {layer.name!r} has no transform; cannot write a GeoTIFF"
        )
    write_geotiff(
        array,
        dest,
        transform=transform,
        crs=layer.crs,
        nodata=(layer.metadata or {}).get("nodata"),
        band_names=[layer.name],
    )
    return dest


def _remove_previous_artifacts(root: Path) -> None:
    manifest_path = root / "manifest.json"
    try:
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    for record in previous.get("layers") or []:
        rel = record.get("path")
        if not rel:
            continue
        if record.get("kind") == "images" and (record.get("metadata") or {}).get(
            "external"
        ):
            continue
        try:
            path = _safe_city_path(root, rel)
        except CityIntegrityError:
            continue
        if path.exists() and path.is_file():
            path.unlink()
    boundary = previous.get("boundary")
    if boundary:
        try:
            bpath = _safe_city_path(root, boundary)
        except CityIntegrityError:
            return
        if bpath.exists():
            bpath.unlink()


def _crs_to_str(crs: Any) -> str | None:
    if crs is None:
        return None
    if hasattr(crs, "to_string"):
        return crs.to_string()
    return str(crs)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _raster_grid_fields(layer: Layer) -> dict[str, Any]:
    if layer.kind != "raster":
        return {}
    data = layer.data
    rio = getattr(data, "rio", None)
    if rio is None:
        return {}
    try:
        transform = rio.transform()
        transform_list = [
            float(transform.a),
            float(transform.b),
            float(transform.c),
            float(transform.d),
            float(transform.e),
            float(transform.f),
        ]
    except Exception:
        transform_list = None
    return {
        "transform": transform_list,
        "width": getattr(rio, "width", None),
        "height": getattr(rio, "height", None),
        "dtype": str(getattr(data, "dtype", "")),
        "nodata": _json_safe(rio.nodata),
    }


def _raster_file_fields(path: Path) -> dict[str, Any]:
    try:
        import rasterio
    except ImportError:
        return {}
    with rasterio.open(path) as src:
        return {
            "transform": [
                float(src.transform.a),
                float(src.transform.b),
                float(src.transform.c),
                float(src.transform.d),
                float(src.transform.e),
                float(src.transform.f),
            ],
            "width": src.width,
            "height": src.height,
            "dtype": src.dtypes[0],
            "nodata": _json_safe(src.nodata),
        }


def _copy_layer_file(layer: Layer, layer_dir: Path) -> str | None:
    src = layer.path
    if not src or not Path(src).exists():
        return None
    dest = layer_dir / Path(src).name
    if Path(src).resolve() != dest.resolve():
        shutil.copy2(src, dest)
    return f"layers/{dest.name}"


def _write_layer(layer: Layer, layer_dir: Path) -> str | None:
    if layer.data is None and layer.path:
        copied = _copy_layer_file(layer, layer_dir)
        if copied:
            return copied
    if layer.kind == "vector":
        if layer.data is None:
            return None
        rel = f"layers/{layer.name}.gpkg"
        layer.data.to_file(layer_dir / f"{layer.name}.gpkg", driver="GPKG")
        return rel
    if layer.kind == "table":
        if layer.data is None:
            return None
        try:
            rel = f"layers/{layer.name}.parquet"
            layer.data.to_parquet(layer_dir / f"{layer.name}.parquet", index=False)
            return rel
        except Exception:
            rel = f"layers/{layer.name}.csv"
            layer.data.to_csv(layer_dir / f"{layer.name}.csv", index=False)
            return rel
    if layer.kind == "raster":
        dest = layer_dir / f"{layer.name}.tif"
        if layer.data is not None and hasattr(layer.data, "rio"):
            layer.data.rio.to_raster(dest)
            return f"layers/{dest.name}"
        if (
            layer.data is not None
            and hasattr(layer.data, "shape")
            and (layer.metadata or {}).get("transform") is not None
        ):
            _save_raster_layer(layer, dest)
            return f"layers/{dest.name}"
        src = layer.path
        if src and Path(src).exists():
            if Path(src).resolve() != dest.resolve():
                shutil.copy2(src, dest)
            return f"layers/{dest.name}"
        return None
    if layer.kind == "graph":
        if layer.data is None:
            return None
        dest = layer_dir / f"{layer.name}.graphml"
        _write_graphml(layer.data, dest)
        return f"layers/{dest.name}"
    if layer.kind == "images":
        if layer.metadata.get("external"):
            return layer.path
        src = layer.path
        if src and Path(src).exists():
            dest = layer_dir / Path(src).name
            if Path(src).resolve() != dest.resolve():
                shutil.copy2(src, dest)
            return f"layers/{dest.name}"
        return layer.path
    return layer.path


def _materialize_layer(layer: Layer) -> Layer:
    """Read a deferred layer payload in place."""
    if not layer.lazy or layer.data is not None:
        return layer
    if not layer.path:
        layer.lazy = False
        return layer
    layer.data = _read_layer(layer.kind, layer.path, {"name": layer.name})
    layer.lazy = False
    return layer


def _read_layer(kind: str, path: str, record: Mapping[str, Any] | None = None) -> Any:
    file_path = Path(path)
    if kind == "vector":
        gpd = _require_geopandas()
        return gpd.read_file(file_path)
    if kind == "table":
        import pandas as pd

        if file_path.suffix.lower() == ".parquet":
            return pd.read_parquet(file_path)
        return pd.read_csv(file_path)
    if kind == "raster":
        from urbancode.errors import MissingExtraError

        try:
            from urbancode.imagery.read import read

            return read(file_path, name=(record or {}).get("name")).data
        except MissingExtraError:
            raise
        except ImportError as exc:
            raise MissingExtraError(
                "rasterio is required for this feature. "
                'Install with: pip install "urbancode[imagery]"'
            ) from exc
    if kind == "graph":
        return _read_graphml(file_path)
    return str(file_path)


def _write_graphml(graph: Any, dest: Path) -> None:
    try:
        import osmnx as ox

        ox.save_graphml(graph, dest)
        return
    except Exception:
        pass
    import networkx as nx

    nx.write_graphml(graph, dest)


def _read_graphml(path: Path) -> Any:
    try:
        import osmnx as ox

        return ox.load_graphml(path)
    except Exception:
        import networkx as nx

        return nx.read_graphml(path)


def handle_layer_error(
    city: City,
    name: str,
    exc: Exception,
    on_error: str,
) -> None:
    """Apply ``on_error`` policy for a failed layer download."""
    if on_error not in {"raise", "warn", "ignore"}:
        raise ValueError("on_error must be 'raise', 'warn', or 'ignore'")
    city.record_error(name, str(exc), type=type(exc).__name__)
    if on_error == "raise":
        raise
    if on_error == "warn":
        import warnings

        warnings.warn(f"layer {name!r} failed: {exc}", stacklevel=2)
