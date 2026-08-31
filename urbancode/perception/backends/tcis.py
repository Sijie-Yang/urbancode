"""TCIS / Thermal Comfort in Sight inference backend.

Torch is imported only when a predict function runs. Training Dataset,
TensorBoard, and research-script metrics stay out of this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from urbancode.streetview.contract import load_manifest

CANONICAL_SCORE = "thermal_affordance"
LEGACY_SCORE = "thermal_comfort"
SCORE_UNIT = "score_0_5"
TRAINING_GEOGRAPHY = (
    "Singapore street-view photos in the Thermal Affordance Dataset"
)


def canonical_output_names(manifest: dict[str, Any] | None = None) -> list[str]:
    """Official UrbanCode names: VATA first, then VPI heads."""
    data = manifest or load_manifest()
    legacy = list(data["output_feature_names"])
    if not legacy:
        return [CANONICAL_SCORE]
    return [CANONICAL_SCORE, *legacy[1:]]


def _require_torch() -> Any:
    from urbancode.errors import require_extra

    return require_extra("torch", "perception")


def _two_stage_model(num_initial_features: int, num_features: int) -> Any:
    torch = _require_torch()
    nn = torch.nn
    models = __import__("torchvision.models", fromlist=["models"])

    class TwoStageNNModel(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.base_model = models.resnet50(
                weights=models.ResNet50_Weights.IMAGENET1K_V1
            )
            self.base_features = self.base_model.fc.in_features
            self.base_model.fc = nn.Identity()
            self.task_layers = nn.Sequential(
                nn.Linear(self.base_features + num_initial_features, 1024),
                nn.ReLU(),
                nn.Dropout(0.5),
                nn.Linear(1024, 512),
                nn.ReLU(),
                nn.Dropout(0.5),
                nn.Linear(512, 256),
                nn.ReLU(),
                nn.Dropout(0.5),
                nn.Linear(256, num_features),
            )
            self.final_layer = nn.Sequential(
                nn.Linear(
                    self.base_features + num_initial_features + num_features, 512
                ),
                nn.ReLU(),
                nn.Dropout(0.5),
                nn.Linear(512, 256),
                nn.ReLU(),
                nn.Dropout(0.5),
                nn.Linear(256, 1),
            )
            self.w = nn.Parameter(torch.tensor(0.5))

        def forward(self, x, initial_features):
            base_output = self.base_model(x)
            combined_input = torch.cat((base_output, initial_features), dim=1)
            features = self.task_layers(combined_input)
            combined_features = torch.cat(
                (base_output, initial_features, features), dim=1
            )
            score = self.final_layer(combined_features)
            return features, score

    return TwoStageNNModel()


def predict_paths(
    paths: list[str] | list[Path],
    *,
    device: str | None = None,
    include_features: bool = True,
) -> pd.DataFrame:
    """Run TCIS on a list of image files. Returns a DataFrame."""
    resolved = [Path(p) for p in paths]
    missing = [str(p) for p in resolved if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"image files not found: {missing[:3]}")
    rows = [
        {
            "Filename": path.name,
            "image_id": path.name,
            "image_path": str(path.resolve()),
        }
        for path in resolved
    ]
    frame = pd.DataFrame(rows)
    parent = str(resolved[0].parent)
    if len({p.parent for p in resolved}) == 1:
        return predict_frame(
            frame, folder_path=parent, device=device, include_features=include_features
        )
    parts = []
    for path in resolved:
        one = frame[frame["image_path"] == str(path.resolve())].copy()
        parts.append(
            predict_frame(
                one,
                folder_path=str(path.parent),
                device=device,
                include_features=include_features,
            )
        )
    return pd.concat(parts, ignore_index=True)


def predict_frame(
    frame: pd.DataFrame,
    *,
    folder_path: str | None = None,
    device: str | None = None,
    include_features: bool = True,
) -> pd.DataFrame:
    """Run TCIS on a catalog table. Delegates to the pinned model chain."""
    from urbancode.perception.backends.tcis_runtime import run_dataset

    return run_dataset(
        frame,
        device=device or "cpu",
        include_features=include_features,
        image_root=folder_path,
    )


def TwoStageNNModel(num_initial_features: int, num_features: int) -> Any:
    """Compatibility constructor used by older streetview imports."""
    return _two_stage_model(num_initial_features, num_features)
