"""Quality flags and provenance receipts."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable
from uuid import uuid4

from urbancode._version import __version__ as PACKAGE_VERSION

FLAG_NODATA = "nodata"
FLAG_LOW_COVERAGE = "low_coverage"
FLAG_PARTIAL_COVERAGE = "partial_coverage"
FLAG_EXPERIMENTAL = "experimental"
FLAG_GEOGRAPHIC_CRS = "geographic_crs"
FLAG_NO_NETWORK = "no_network"
FLAG_NO_OBSERVATION = "no_observation"

LOW_COVERAGE = 0.1


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(math.isnan(float(value)))
    except (TypeError, ValueError):
        return False


def clip_coverage(coverage: float | None) -> float | None:
    """Clamp a computed fraction. User-supplied coverage must use ``require_coverage``."""
    if coverage is None or is_missing(coverage):
        return None
    return max(0.0, min(1.0, float(coverage)))


def require_coverage(coverage: float | None) -> float | None:
    """Return coverage in ``[0, 1]`` or null. Out-of-range values raise."""
    if coverage is None or is_missing(coverage):
        return None
    value = float(coverage)
    if value < 0.0 or value > 1.0:
        raise ValueError(f"coverage must be in [0, 1] or null; got {value}")
    return value


def quality_flags(
    *,
    value: Any = None,
    coverage: float | None = None,
    experimental: bool = False,
    extra: Iterable[str] | None = None,
) -> list[str]:
    """Build a flag list. Missing is ``nodata``, never coerced to 0."""
    flags: list[str] = []
    if is_missing(value):
        flags.append(FLAG_NODATA)
    cov = clip_coverage(coverage)
    if cov is not None and cov < LOW_COVERAGE:
        flags.append(FLAG_LOW_COVERAGE)
    if cov is not None and 0.0 < cov < 1.0:
        flags.append(FLAG_PARTIAL_COVERAGE)
    if experimental:
        flags.append(FLAG_EXPERIMENTAL)
    for item in extra or []:
        if item and item not in flags:
            flags.append(str(item))
    return flags


def merge_flags(*groups: Iterable[str] | None) -> list[str]:
    seen: list[str] = []
    for group in groups:
        for item in group or []:
            if item and item not in seen:
                seen.append(str(item))
    return seen


def coverage_fraction(valid: int, total: int) -> float:
    if total <= 0:
        return float("nan")
    return clip_coverage(float(valid) / float(total)) or 0.0


@dataclass
class ProvenanceRecord:
    """One compute or acquire step."""

    provenance_id: str = ""
    source: str | None = None
    source_uri: str | None = None
    source_version: str | None = None
    method: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    input_fingerprints: dict[str, str] = field(default_factory=dict)
    parent_layer_ids: list[str] = field(default_factory=list)
    backend: str | None = None
    backend_version: str | None = None
    created_at: str = ""
    software_version: str = PACKAGE_VERSION
    crs: str | None = None
    units: str | None = None
    assumptions: list[str] = field(default_factory=list)
    license: str | None = None

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.provenance_id:
            payload = json.dumps(asdict(self), sort_keys=True, default=str)
            digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
            self.provenance_id = f"prov:{digest}:{uuid4().hex[:8]}"

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


def stamp_layer(layer: Any, *, method: str | None = None, **extra: Any) -> ProvenanceRecord:
    """Attach a provenance receipt to ``layer.metadata``."""
    processing = dict((getattr(layer, "metadata", None) or {}).get("processing") or {})
    assumptions = list(extra.pop("assumptions", []) or [])
    rec = ProvenanceRecord(
        source=getattr(layer, "source", None),
        method=method or processing.get("op") or processing.get("method"),
        parameters={**processing, **extra},
        parent_layer_ids=[str(processing["parent"])] if processing.get("parent") else [],
        backend=processing.get("backend"),
        crs=_crs_text(getattr(layer, "crs", None)),
        units=(getattr(layer, "metadata", None) or {}).get("unit"),
        assumptions=assumptions,
    )
    metadata = getattr(layer, "metadata", None)
    if metadata is not None:
        metadata["provenance_id"] = rec.provenance_id
        metadata.setdefault("provenance", rec.to_record())
    return rec


def _crs_text(crs: Any) -> str | None:
    if crs is None:
        return None
    if hasattr(crs, "to_string"):
        return crs.to_string()
    return str(crs)
