"""IndicatorRecord / IndicatorResult — unified compute output."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import pandas as pd

from urbancode.city import Layer
from urbancode.errors import require_extra
from urbancode.provenance import is_missing, merge_flags, quality_flags, require_coverage
from urbancode.units import AnalysisUnits


@dataclass
class IndicatorRecord:
    """One indicator value on one analysis unit."""

    city_id: str
    unit_id: str
    indicator: str
    value: float | None
    unit: str | None = None
    dimension: str | None = None
    time: str | None = None
    method: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    source: str | None = None
    coverage: float | None = None
    uncertainty: float | None = None
    quality_flags: list[str] = field(default_factory=list)
    provenance_id: str | None = None

    def __post_init__(self) -> None:
        if is_missing(self.value):
            self.value = None
        self.coverage = require_coverage(self.coverage)
        auto = quality_flags(value=self.value, coverage=self.coverage)
        self.quality_flags = merge_flags(auto, self.quality_flags)


@dataclass
class IndicatorResult:
    """A table of IndicatorRecords, optionally joined to AnalysisUnits."""

    records: list[IndicatorRecord] = field(default_factory=list)
    units: AnalysisUnits | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    on_duplicate: str = "raise"

    def __post_init__(self) -> None:
        self._check_keys()

    def _check_keys(self) -> None:
        seen: dict[tuple[str, str, str, str], int] = {}
        for rec in self.records:
            key = (rec.city_id, rec.unit_id, rec.indicator, rec.time or "")
            seen[key] = seen.get(key, 0) + 1
        dups = [key for key, n in seen.items() if n > 1]
        if dups and self.on_duplicate == "raise":
            raise ValueError(
                "duplicate IndicatorResult keys "
                "(city_id, unit_id, indicator, time); "
                f"examples={dups[:3]!r}. Pass on_duplicate='keep' to allow."
            )

    def _require_indicator(self, indicator: str | None) -> str:
        names = {rec.indicator for rec in self.records}
        if indicator is not None:
            if names and indicator not in names:
                raise KeyError(f"unknown indicator {indicator!r}; have {sorted(names)}")
            return indicator
        if len(names) > 1:
            raise ValueError(
                "multiple indicators present; pass indicator= to to_layer() / plot()"
            )
        return next(iter(names), "indicator")

    def to_pandas(self) -> pd.DataFrame:
        rows = []
        for rec in self.records:
            row = asdict(rec)
            row["quality_flags"] = list(rec.quality_flags)
            row["parameters"] = dict(rec.parameters)
            rows.append(row)
        columns = [
            "city_id",
            "unit_id",
            "indicator",
            "value",
            "unit",
            "time",
            "coverage",
            "quality_flags",
            "method",
            "parameters",
            "provenance_id",
            "dimension",
            "source",
            "uncertainty",
        ]
        if not rows:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame(rows)

    def to_geopandas(self, indicator: str | None = None) -> Any:
        gpd = require_extra("geopandas", "vector")
        if self.units is None:
            raise ValueError("to_geopandas requires AnalysisUnits on this result")
        table = self.to_pandas()
        if indicator is not None:
            table = table[table["indicator"] == indicator]
        frame = self.units.frame.copy()
        merged = frame.merge(table, on="unit_id", how="left")
        return gpd.GeoDataFrame(merged, geometry=frame.geometry.name, crs=frame.crs)

    def to_xarray(self) -> Any:
        xr = require_extra("xarray", "imagery")
        table = self.to_pandas()
        if "time" in table.columns and table["time"].map(is_missing).all():
            table = table.drop(columns=["time"])
        index = [
            c for c in ("city_id", "unit_id", "indicator", "time") if c in table.columns
        ]
        indexed = table.set_index(index if index else "unit_id")
        return xr.Dataset.from_dataframe(indexed)

    def to_layer(self, name: str | None = None, *, indicator: str | None = None) -> Layer:
        chosen = self._require_indicator(indicator or name)
        subset = IndicatorResult(
            records=[r for r in self.records if r.indicator == chosen],
            units=self.units,
            metadata=dict(self.metadata),
        )
        if self.units is not None:
            frame = subset.to_geopandas(indicator=chosen)
            unit = next((rec.unit for rec in subset.records if rec.unit), None)
            return Layer(
                name=chosen,
                kind="vector",
                data=frame,
                crs=getattr(frame, "crs", None),
                source="urbancode.indicators",
                metadata={
                    "column": "value",
                    "unit": unit,
                    "indicator": chosen,
                    **dict(self.metadata),
                },
            )
        return Layer(
            name=chosen,
            kind="table",
            data=subset.to_pandas(),
            source="urbancode.indicators",
            metadata=dict(self.metadata),
        )

    def plot(
        self,
        save: str | Path | None = None,
        *,
        indicator: str | None = None,
        ax: Any = None,
        context: Any = None,
        **style: Any,
    ) -> Any:
        if context is not None:
            style.setdefault("context", context)
        return self.to_layer(indicator=indicator).plot(
            save=save, column="value", ax=ax, **style
        )

    def save(self, directory: str | Path) -> Path:
        """Write records (CSV + optional parquet), result.json, and units.gpkg."""
        out = Path(directory)
        out.mkdir(parents=True, exist_ok=True)
        table = self.to_pandas()
        csv_table = table.copy()
        csv_table["parameters"] = csv_table["parameters"].map(
            lambda p: json.dumps(p, default=str) if isinstance(p, (dict, list)) else p
        )
        csv_table["quality_flags"] = csv_table["quality_flags"].map(
            lambda flags: json.dumps(flags) if isinstance(flags, list) else flags
        )
        csv_table.to_csv(out / "records.csv", index=False)
        storage = "csv"
        try:
            table.to_parquet(out / "records.parquet", index=False)
            storage = "parquet"
        except Exception as exc:
            storage = "csv"
            self.metadata.setdefault("storage_fallback", f"csv ({exc})")
        receipts = [
            item
            for item in (self.metadata.get("provenance") or [])
            if isinstance(item, dict)
        ]
        prov = out / "provenance"
        prov.mkdir(exist_ok=True)
        (prov / "receipts.jsonl").write_text(
            "".join(json.dumps(item, default=str) + "\n" for item in receipts),
            encoding="utf-8",
        )
        meta = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "n_records": len(self.records),
            "storage": storage,
            "metadata": self.metadata,
            "units": None
            if self.units is None
            else {
                "city_id": self.units.city_id,
                "kind": self.units.kind,
                "cell_size": self.units.cell_size,
                "crs": self.units.crs,
                "metric_crs": self.units.metric_crs,
                "scheme": (self.units.metadata or {}).get("scheme"),
            },
        }
        (out / "result.json").write_text(
            json.dumps(meta, indent=2, default=str), encoding="utf-8"
        )
        if self.units is not None:
            self.units.frame.to_file(out / "units.gpkg", driver="GPKG")
        return out

    @classmethod
    def load(cls, directory: str | Path) -> IndicatorResult:
        root = Path(directory)
        parquet = root / "records.parquet"
        if parquet.exists():
            try:
                table = pd.read_parquet(parquet)
            except Exception:
                table = pd.read_csv(root / "records.csv")
        else:
            table = pd.read_csv(root / "records.csv")
        records = [_record_from_row(row) for row in table.to_dict(orient="records")]
        meta: dict[str, Any] = {}
        units = None
        result_path = root / "result.json"
        if result_path.exists():
            packed = json.loads(result_path.read_text(encoding="utf-8"))
            meta = dict(packed.get("metadata") or {})
        receipts_path = root / "provenance" / "receipts.jsonl"
        if receipts_path.exists() and "provenance" not in meta:
            meta["provenance"] = [
                json.loads(line)
                for line in receipts_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        units_path = root / "units.gpkg"
        if units_path.exists():
            gpd = require_extra("geopandas", "vector")
            frame = gpd.read_file(units_path)
            info = {}
            if result_path.exists():
                info = json.loads(result_path.read_text(encoding="utf-8")).get("units") or {}
            units = AnalysisUnits(
                frame=frame,
                city_id=str(info.get("city_id") or "city"),
                kind=str(info.get("kind") or "grid"),
                cell_size=info.get("cell_size"),
                crs=str(info.get("crs") or getattr(frame, "crs", "") or ""),
                metric_crs=str(info.get("metric_crs") or ""),
            )
        return cls(records=records, units=units, metadata=meta)


def _record_from_row(row: dict[str, Any]) -> IndicatorRecord:
    flags = row.get("quality_flags")
    if isinstance(flags, str):
        try:
            parsed = json.loads(flags)
            flag_list = list(parsed) if isinstance(parsed, list) else [p for p in flags.split("|") if p]
        except json.JSONDecodeError:
            flag_list = [p for p in flags.split("|") if p]
    elif isinstance(flags, list):
        flag_list = list(flags)
    else:
        flag_list = []
    params = row.get("parameters")
    if isinstance(params, str) and params:
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            params = {"raw": params}
    if not isinstance(params, dict):
        params = {}
    value = row.get("value")
    if is_missing(value):
        value = None
    elif value is not None:
        value = float(value)
    coverage = row.get("coverage")
    if is_missing(coverage):
        coverage = None
    elif coverage is not None:
        coverage = float(coverage)
    return IndicatorRecord(
        city_id=str(row.get("city_id") or "city"),
        unit_id=str(row.get("unit_id") or ""),
        indicator=str(row.get("indicator") or ""),
        value=value,
        unit=None if is_missing(row.get("unit")) else row.get("unit"),
        dimension=None if is_missing(row.get("dimension")) else row.get("dimension"),
        time=None if is_missing(row.get("time")) else row.get("time"),
        method=None if is_missing(row.get("method")) else row.get("method"),
        parameters=params,
        source=None if is_missing(row.get("source")) else row.get("source"),
        coverage=coverage,
        uncertainty=None
        if is_missing(row.get("uncertainty"))
        else row.get("uncertainty"),
        quality_flags=flag_list,
        provenance_id=None
        if is_missing(row.get("provenance_id"))
        else row.get("provenance_id"),
    )


def from_records(
    records: Sequence[IndicatorRecord] | Iterable[IndicatorRecord],
    *,
    units: AnalysisUnits | None = None,
    metadata: dict[str, Any] | None = None,
    on_duplicate: str = "raise",
) -> IndicatorResult:
    return IndicatorResult(
        records=list(records),
        units=units,
        metadata=dict(metadata or {}),
        on_duplicate=on_duplicate,
    )
