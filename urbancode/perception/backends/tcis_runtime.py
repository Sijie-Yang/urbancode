"""Dataset-scale TCIS inference. Torch is imported only when a chain loads."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import signal
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from urbancode._version import __version__ as PACKAGE_VERSION
from urbancode.perception.backends.tcis import (
    CANONICAL_SCORE,
    LEGACY_SCORE,
    SCORE_UNIT,
    TRAINING_GEOGRAPHY,
    _two_stage_model,
    canonical_output_names,
)
from urbancode.streetview.contract import (
    ContractError,
    initial_features_from_frame,
    load_feature_models_manifest,
    load_feature_stats,
    load_manifest,
    normalize_initial_features,
)
from urbancode.streetview.features import COLOR_FEATURE_NAMES, extract_features
from urbancode.streetview.places365 import (
    ensure_places365_weights,
    load_places365_manifest,
    places365_labels,
)
from urbancode.streetview.weights import ensure_tcis_artifacts, load_validated_state_dict

_EXPORT_DROP = {"image_path", "image_uri"}
_STOP = False


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit() -> str | None:
    try:
        import subprocess

        root = Path(__file__).resolve().parents[3]
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except Exception:
        return None


def _dependency_versions() -> dict[str, str]:
    versions: dict[str, str] = {"urbancode": PACKAGE_VERSION}
    for name in ("torch", "torchvision", "transformers", "cv2", "PIL"):
        try:
            if name == "cv2":
                import cv2

                versions["opencv"] = getattr(cv2, "__version__", "unknown")
            elif name == "PIL":
                import PIL

                versions["pillow"] = getattr(PIL, "__version__", "unknown")
            else:
                module = __import__(name)
                versions[name] = getattr(module, "__version__", "unknown")
        except Exception:
            continue
    return versions


def _resolve_device(device: str | None, torch: Any) -> str:
    if device:
        return device
    return "cuda" if torch.cuda.is_available() else "cpu"


def _cuda_info(torch: Any, device: str) -> dict[str, Any]:
    info: dict[str, Any] = {
        "device": device,
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_version": getattr(torch.version, "cuda", None),
    }
    if device.startswith("cuda") and torch.cuda.is_available():
        index = torch.cuda.current_device()
        info["gpu_name"] = torch.cuda.get_device_name(index)
        info["gpu_index"] = int(index)
        info["gpu_memory_total_mb"] = round(
            torch.cuda.get_device_properties(index).total_memory / (1024 * 1024), 1
        )
    return info


def resolve_image_path(row: Any, image_root: str | Path | None = None) -> Path | None:
    candidates: list[Path] = []
    for key in ("image_path", "image_uri"):
        value = row.get(key) if hasattr(row, "get") else None
        if value:
            candidates.append(Path(str(value)))
    rel = None
    for key in ("relative_path", "Filename", "filename"):
        value = row.get(key) if hasattr(row, "get") else None
        if value:
            rel = str(value).replace("\\", "/")
            break
    if image_root and rel:
        candidates.append(Path(image_root) / rel)
    for path in candidates:
        if path.is_file():
            return path
    return candidates[0] if candidates else None


def _atomic_parquet(frame: pd.DataFrame, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    frame.to_parquet(tmp, index=False)
    os.replace(tmp, dest)


def _atomic_json(payload: dict[str, Any], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, dest)


def _export_frame(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    drop = [name for name in _EXPORT_DROP if name in out.columns]
    if hasattr(out, "geometry"):
        drop.append(getattr(out, "geometry").name if hasattr(out.geometry, "name") else "geometry")
    if "geometry" in out.columns and "geometry" not in drop:
        drop.append("geometry")
    drop = [name for name in drop if name in getattr(out, "columns", [])]
    if drop:
        out = out.drop(columns=drop)
    if hasattr(out, "to_wgs84") or str(type(out)).endswith("GeoDataFrame'>"):
        out = pd.DataFrame(out)
    return pd.DataFrame(out)


def _completed_ids(output: Path) -> set[str]:
    ids: set[str] = set()
    if output.is_file():
        try:
            existing = pd.read_parquet(output, columns=["image_id"])
            ids.update(existing["image_id"].astype(str))
        except Exception:
            pass
    chunk_dir = output.with_name(output.stem + "_chunks")
    if chunk_dir.is_dir():
        for path in sorted(chunk_dir.glob("chunk_*.parquet")):
            try:
                part = pd.read_parquet(path, columns=["image_id"])
                ids.update(part["image_id"].astype(str))
            except Exception:
                continue
    return ids


class TCISChain:
    """Load SegFormer, Faster R-CNN, Places365, and TCIS once."""

    def __init__(self, device: str = "cpu", batch_size: int = 1) -> None:
        torch = __import__("torch")
        self.torch = torch
        self.device = _resolve_device(device, torch)
        self.batch_size = max(1, int(batch_size))
        self.tcis_manifest = load_manifest()
        self.feature_manifest = load_feature_models_manifest()
        self.output_names = canonical_output_names(self.tcis_manifest)
        self.if_names = list(self.tcis_manifest["initial_feature_names"])
        self.height, self.width = self.tcis_manifest["image_size"]
        self.weights_path, self.stats_path = ensure_tcis_artifacts()
        self.mins, self.maxs = load_feature_stats(
            self.stats_path, n_features=len(self.if_names)
        )
        self._load_segformer()
        self._load_detector()
        self._load_places365()
        self._load_tcis()
        self.provenance = self._provenance()

    def _load_segformer(self) -> None:
        from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor

        spec = self.feature_manifest["segformer"]
        revision = spec["revision"]
        self.seg_processor = SegformerImageProcessor.from_pretrained(
            spec["processor"], revision=revision
        )
        self.seg_model = SegformerForSemanticSegmentation.from_pretrained(
            spec["model"], revision=revision
        )
        self.seg_model.to(self.device)
        self.seg_model.eval()
        self.seg_classes = list(spec["classes"])

    def _load_detector(self) -> None:
        from torchvision.models.detection import (
            FasterRCNN_ResNet50_FPN_Weights,
            fasterrcnn_resnet50_fpn,
        )

        spec = self.feature_manifest["faster_rcnn"]
        weights = FasterRCNN_ResNet50_FPN_Weights.COCO_V1
        self.detector = fasterrcnn_resnet50_fpn(weights=weights)
        self.detector.to(self.device)
        self.detector.eval()
        self.det_threshold = float(spec.get("score_threshold", 0.0))
        self.det_labels = {
            1: "person",
            2: "bicycle",
            3: "car",
            4: "motorcycle",
            6: "bus",
            8: "truck",
            10: "traffic light",
            11: "fire hydrant",
            13: "stop sign",
            15: "bench",
        }

    def _load_places365(self) -> None:
        from urbancode.streetview.features import SCENE_CATEGORIES

        torch = self.torch
        models = __import__("torchvision.models", fromlist=["models"])
        weights = ensure_places365_weights()
        labels = places365_labels()
        model = models.resnet50(num_classes=365)
        checkpoint = torch.load(weights, map_location="cpu")
        state = {
            str.replace(key, "module.", ""): value
            for key, value in checkpoint["state_dict"].items()
        }
        model.load_state_dict(state)
        model.to(self.device)
        model.eval()
        self.places_model = model
        with labels.open(encoding="utf-8") as handle:
            categories = [line.strip().split(" ")[0][3:] for line in handle]
        self.scene_categories = list(SCENE_CATEGORIES)
        self.scene_indices = [categories.index(name) for name in self.scene_categories]
        self.places_weights = weights
        self.places_labels = labels

    def _load_tcis(self) -> None:
        from torchvision import transforms

        model = _two_stage_model(
            num_initial_features=int(self.tcis_manifest["num_initial_features"]),
            num_features=int(self.tcis_manifest["num_head_features"]),
        )
        state = load_validated_state_dict(self.weights_path, map_location=self.device)
        model.load_state_dict(state)
        model.to(self.device)
        model.eval()
        self.tcis_model = model
        self.tcis_transform = transforms.Compose(
            [
                transforms.Resize((self.height, self.width)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )
        self.places_transform = transforms.Compose(
            [
                transforms.Resize((256, 256)),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )
        self.det_transform = transforms.ToTensor()

    def _provenance(self) -> dict[str, Any]:
        places = load_places365_manifest()
        seg = self.feature_manifest["segformer"]
        det = self.feature_manifest["faster_rcnn"]
        return {
            "model_id": "tcis-twostage-resnet50",
            "model_version": self.tcis_manifest.get("model_version"),
            "model_revision": self.tcis_manifest.get("revision"),
            "architecture": self.tcis_manifest.get("architecture"),
            "weights_sha256": self.tcis_manifest.get("weights_sha256"),
            "feature_stats_sha256": self.tcis_manifest.get("stats_sha256"),
            "hf_model": self.tcis_manifest.get("hf_model"),
            "hf_dataset": self.tcis_manifest.get("hf_dataset"),
            "training_geography": TRAINING_GEOGRAPHY,
            "device": self.device,
            "urbancode_version": PACKAGE_VERSION,
            "git_commit": _git_commit(),
            "output_indicators": self.output_names,
            "output_unit": SCORE_UNIT,
            "canonical_score": CANONICAL_SCORE,
            "legacy_score_alias": LEGACY_SCORE,
            "segformer_model": seg["model"],
            "segformer_processor": seg["processor"],
            "segformer_revision": seg["revision"],
            "faster_rcnn_weights": det["weights"],
            "faster_rcnn_score_threshold": det.get("score_threshold", 0.0),
            "places365_weights_sha256": places.get("sha256"),
            "places365_labels_sha256": places.get("labels_sha256"),
            "dependencies": _dependency_versions(),
            "cuda": _cuda_info(self.torch, self.device),
        }

    def predict_frame(
        self,
        frame: pd.DataFrame,
        *,
        image_root: str | Path | None = None,
        include_features: bool = True,
        workers: int = 0,
    ) -> pd.DataFrame:
        if frame is None or frame.empty:
            raise ValueError("TCIS predict needs a non-empty DataFrame")
        df = frame.copy()
        if "image_id" not in df.columns:
            if "Filename" in df.columns:
                df["image_id"] = df["Filename"].astype(str)
            elif "image_path" in df.columns:
                df["image_id"] = [Path(p).name for p in df["image_path"]]
            else:
                raise ValueError("TCIS predict needs image_id, Filename, or image_path")
        if "relative_path" not in df.columns:
            if "Filename" in df.columns:
                df["relative_path"] = df["Filename"].astype(str)
            elif "image_path" in df.columns:
                df["relative_path"] = [Path(p).name for p in df["image_path"]]
        if "Filename" not in df.columns:
            df["Filename"] = [Path(str(p)).name for p in df["relative_path"]]

        rows = [row for _, row in df.iterrows()]
        extracted: list[dict[str, Any]] = []
        for start in range(0, len(rows), self.batch_size):
            extracted.extend(
                self._predict_batch(rows[start : start + self.batch_size], image_root)
            )
        features = pd.DataFrame(extracted)
        merged = df.reset_index(drop=True)
        for column in features.columns:
            merged[column] = features[column].to_numpy()

        ok = merged["error"].isna() if "error" in merged.columns else pd.Series(True, index=merged.index)
        for name in self.output_names:
            if name not in merged.columns:
                merged[name] = np.nan
        merged[LEGACY_SCORE] = merged.get(CANONICAL_SCORE, np.nan)

        if ok.any():
            from PIL import Image

            ok_frame = merged.loc[ok].reset_index(drop=True)
            initial = initial_features_from_frame(ok_frame, self.if_names)
            normalized = normalize_initial_features(initial, self.mins, self.maxs)
            public_heads = self.output_names[1:]
            score_out = np.full(len(ok_frame), np.nan, dtype=float)
            head_out = np.full((len(ok_frame), len(public_heads)), np.nan, dtype=float)
            step = max(int(self.batch_size), 1)
            for start in range(0, len(ok_frame), step):
                batch = ok_frame.iloc[start : start + step]
                images = []
                for _, row in batch.iterrows():
                    path = resolve_image_path(row, image_root)
                    image = Image.open(path).convert("RGB")
                    images.append(self.tcis_transform(image))
                tensor = self.torch.stack(images).to(self.device)
                feats = self.torch.tensor(
                    normalized[start : start + len(batch)],
                    dtype=self.torch.float32,
                ).to(self.device)
                with self.torch.no_grad():
                    heads, scores = self.tcis_model(tensor, feats)
                scores = scores.squeeze(-1).detach().cpu().numpy()
                heads = heads.detach().cpu().numpy()
                if heads.shape[1] != len(public_heads):
                    raise ContractError(
                        f"model head size {heads.shape[1]} != {len(public_heads)}"
                    )
                score_out[start : start + len(scores)] = scores
                head_out[start : start + len(heads)] = heads
            merged.loc[ok, CANONICAL_SCORE] = score_out
            merged.loc[ok, LEGACY_SCORE] = score_out
            for i, name in enumerate(public_heads):
                merged.loc[ok, name] = head_out[:, i]

        if not include_features:
            drop = [name for name in self.if_names if name in merged.columns]
            merged = merged.drop(columns=drop, errors="ignore")
        merged.attrs["tcis_provenance"] = dict(self.provenance)
        return merged

    def _predict_batch(
        self, rows: list[Any], image_root: str | Path | None
    ) -> list[dict[str, Any]]:
        from PIL import Image

        loaded: list[tuple[int, Any, Path]] = []
        results: list[dict[str, Any]] = [
            {name: np.nan for name in self.if_names} for _ in rows
        ]
        for i, row in enumerate(rows):
            path = resolve_image_path(row, image_root)
            if path is None or not path.is_file():
                results[i]["error"] = f"image not found: {path}"
                continue
            try:
                image = Image.open(path).convert("RGB")
                color = extract_features(str(path))
                results[i].update(color)
                loaded.append((i, image, path))
            except Exception as exc:
                results[i]["error"] = f"{type(exc).__name__}: {exc}"

        if not loaded:
            return results

        indices = [item[0] for item in loaded]
        images = [item[1] for item in loaded]
        try:
            seg = self._segment_batch(images)
            det = self._detect_batch(images)
            scene = self._scene_batch(images)
        except Exception:
            seg, det, scene = [], [], []
            for image in images:
                try:
                    seg.append(self._segment_batch([image])[0])
                    det.append(self._detect_batch([image])[0])
                    scene.append(self._scene_batch([image])[0])
                except Exception as exc:
                    seg.append({})
                    det.append({})
                    scene.append({"error": f"{type(exc).__name__}: {exc}"})
        for i, one_seg, one_det, one_scene in zip(indices, seg, det, scene):
            results[i].update(one_seg)
            results[i].update(one_det)
            error = one_scene.pop("error", None)
            results[i].update(one_scene)
            if error:
                results[i]["error"] = error
            elif "error" not in results[i]:
                results[i]["error"] = None
        return results

    def _segment_batch(self, images: list[Any]) -> list[dict[str, float]]:
        inputs = self.seg_processor(images=images, return_tensors="pt")
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        with self.torch.no_grad():
            logits = self.seg_model(**inputs).logits
        out = []
        for i, image in enumerate(images):
            upsampled = self.torch.nn.functional.interpolate(
                logits[i : i + 1],
                size=image.size[::-1],
                mode="bilinear",
                align_corners=False,
            )
            pred = upsampled.argmax(dim=1)[0].detach().cpu().numpy()
            total = pred.size
            ratios = {}
            for index, name in enumerate(self.seg_classes):
                ratios[f"seg_{name}"] = float((pred == index).sum() / total)
            out.append(ratios)
        return out

    def _detect_batch(self, images: list[Any]) -> list[dict[str, int]]:
        tensors = [self.det_transform(image).to(self.device) for image in images]
        with self.torch.no_grad():
            predictions = self.detector(tensors)
        out = []
        for pred in predictions:
            counts = {f"det_{label}": 0 for label in self.det_labels.values()}
            labels = pred["labels"]
            scores = pred.get("scores")
            for j, label in enumerate(labels):
                if scores is not None and float(scores[j]) < self.det_threshold:
                    continue
                name = self.det_labels.get(int(label.item()))
                if name:
                    counts[f"det_{name}"] += 1
            out.append(counts)
        return out

    def _scene_batch(self, images: list[Any]) -> list[dict[str, float]]:
        tensor = self.torch.stack(
            [self.places_transform(image) for image in images]
        ).to(self.device)
        with self.torch.no_grad():
            logits = self.places_model(tensor)
            probs = self.torch.nn.functional.softmax(logits, dim=1)
        selected = probs[:, self.scene_indices].detach().cpu().numpy()
        out = []
        for row in selected:
            out.append(
                {
                    f"scene_{name}": float(value)
                    for name, value in zip(self.scene_categories, row)
                }
            )
        return out


def _install_stop_handler() -> Any:
    previous = signal.getsignal(signal.SIGINT)

    def _handle(signum, frame):  # noqa: ARG001
        global _STOP
        _STOP = True

    try:
        signal.signal(signal.SIGINT, _handle)
    except Exception:
        return previous
    return previous


def run_dataset(
    frame: pd.DataFrame,
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
    command: str | None = None,
) -> pd.DataFrame:
    """Run TCIS with optional chunked, resumable writes."""
    global _STOP
    _STOP = False
    if frame is None or frame.empty:
        raise ValueError("TCIS predict needs a non-empty DataFrame")
    work = pd.DataFrame(_export_frame(frame.copy()))
    if "image_id" not in work.columns:
        raise ValueError("dataset-scale TCIS needs unique image_id values")
    work["image_id"] = work["image_id"].astype(str)
    if work["image_id"].duplicated().any():
        raise ValueError("image_id values must be unique")

    dest = Path(output) if output else None
    completed: set[str] = set()
    if dest is not None and resume:
        completed = _completed_ids(dest)
    pending = work[~work["image_id"].isin(completed)].copy()
    skipped = int(len(work) - len(pending))
    run = run_id or uuid.uuid4().hex
    started = _utc_now()
    t0 = time.perf_counter()
    if pending.empty and dest is not None:
        frames = []
        if dest.is_file():
            frames.append(pd.read_parquet(dest))
        chunk_dir = dest.with_name(dest.stem + "_chunks")
        if chunk_dir.is_dir():
            frames.extend(
                pd.read_parquet(path)
                for path in sorted(chunk_dir.glob("chunk_*.parquet"))
            )
        if not frames:
            raise FileNotFoundError(f"resume found no rows for {dest}")
        predicted_all = pd.concat(frames, ignore_index=True).drop_duplicates(
            "image_id", keep="last"
        )
        _atomic_parquet(_export_frame(predicted_all), dest)
        predicted_all.attrs["tcis_provenance"] = {
            "model_run_id": run,
            "resume": True,
            "skipped": skipped,
            "processed": 0,
            "failed": 0,
        }
        return predicted_all
    previous = _install_stop_handler()
    chain = TCISChain(device=device, batch_size=batch_size)
    size = int(chunk_size or len(pending) or 1)
    parts: list[pd.DataFrame] = []
    processed = 0
    failed = 0
    chunk_dir = dest.with_name(dest.stem + "_chunks") if dest is not None else None
    try:
        for start in range(0, len(pending), size):
            if _STOP:
                break
            chunk = pending.iloc[start : start + size]
            predicted = chain.predict_frame(
                chunk,
                image_root=image_root,
                include_features=include_features,
                workers=workers,
            )
            predicted["model_run_id"] = run
            if "error" not in predicted.columns:
                predicted["error"] = None
            predicted["quality_flags"] = [
                "failed" if pd.notna(err) and str(err) else None
                for err in predicted["error"]
            ]
            exported = _export_frame(predicted)
            parts.append(exported)
            processed += int(len(exported))
            failed += int(exported["error"].notna().sum()) if "error" in exported.columns else 0
            if dest is not None and chunk_dir is not None:
                index = start // size
                _atomic_parquet(exported, chunk_dir / f"chunk_{index:05d}.parquet")
                _write_run_manifest(
                    dest,
                    chain=chain,
                    run_id=run,
                    started=started,
                    processed=processed + skipped,
                    failed=failed,
                    skipped=skipped,
                    pending=int(len(pending) - processed),
                    command=command,
                    stopped=_STOP,
                )
    finally:
        try:
            signal.signal(signal.SIGINT, previous)
        except Exception:
            pass

    predicted_all = pd.concat(parts, ignore_index=True) if parts else pending.iloc[0:0]
    if dest is not None:
        frames: list[pd.DataFrame] = []
        if dest.is_file():
            try:
                frames.append(pd.read_parquet(dest))
            except Exception:
                pass
        if chunk_dir is not None and chunk_dir.is_dir():
            frames.extend(
                pd.read_parquet(path)
                for path in sorted(chunk_dir.glob("chunk_*.parquet"))
            )
        if parts:
            frames.extend(parts)
        if frames:
            predicted_all = pd.concat(frames, ignore_index=True)
            predicted_all = predicted_all.drop_duplicates("image_id", keep="last")
        _atomic_parquet(predicted_all, dest)
    elapsed = time.perf_counter() - t0
    provenance = dict(chain.provenance)
    provenance.update(
        {
            "model_run_id": run,
            "started": started,
            "finished": _utc_now(),
            "elapsed_s": round(elapsed, 3),
            "processed": processed,
            "failed": failed,
            "skipped": skipped,
            "batch_size": batch_size,
            "chunk_size": size,
            "resume": resume,
            "command": command,
            "stopped": _STOP,
            "host": platform.node(),
        }
    )
    predicted_all.attrs["tcis_provenance"] = provenance
    if dest is not None:
        _write_run_manifest(
            dest,
            chain=chain,
            run_id=run,
            started=started,
            processed=processed + skipped,
            failed=failed,
            skipped=skipped,
            pending=int(len(work) - processed - skipped),
            command=command,
            stopped=_STOP,
            extra=provenance,
        )
    return predicted_all


def _write_run_manifest(
    output: Path,
    *,
    chain: TCISChain,
    run_id: str,
    started: str,
    processed: int,
    failed: int,
    skipped: int,
    pending: int,
    command: str | None,
    stopped: bool,
    extra: dict[str, Any] | None = None,
) -> None:
    payload = {
        "model_run_id": run_id,
        "started": started,
        "updated": _utc_now(),
        "processed": processed,
        "failed": failed,
        "skipped": skipped,
        "pending": pending,
        "stopped": stopped,
        "command": command,
        "model": chain.provenance,
    }
    if extra:
        payload.update(extra)
    _atomic_json(payload, output.with_name(output.stem + "_run.json"))


def peak_gpu_memory_mb(device: str) -> float | None:
    if not device.startswith("cuda"):
        return None
    try:
        torch = __import__("torch")
        if not torch.cuda.is_available():
            return None
        return round(torch.cuda.max_memory_allocated() / (1024 * 1024), 1)
    except Exception:
        return None
