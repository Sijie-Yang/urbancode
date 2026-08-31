"""Docs figure builder for Heat Resilience in Sight. Not a tutorial.

Copy the snippet on docs/workflows/research_cases/heat_resilience_in_sight
instead of importing this file.

Eight-city application, not a validation of VATA, UTCI, or SHR.
VATA is visual thermal affordance. UTCI is a physical heat-stress index.
SHR is supply minus climate-adjusted demand. They are not substitutes.

Singapore n=21,772 is the HRIS panel. It is not the TCIS survey set
(n=92,233). Hong Kong June–August is a normative anchor, not a
physiological threshold. Monthly demand is an hourly climatological
proxy (ERA5-Land 10–17 local, SolarCal open-sun MRT), not a
street-canyon simulation.

No public SHR or climate-demand helper in this release.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from examples.recipes._common import STATIC_WORKFLOWS
from examples.research_cases._hris_data import (
    CITATION,
    CITY_ORDER,
    D_REF,
    ROOT,
    SINGAPORE_N,
    TCIS_SINGAPORE_N,
    V_REF,
    load_annual,
    load_calibration,
    load_city_stats,
    load_domain_shift,
    load_manifest,
    load_monthly,
    load_sign_stability,
)

STATIC_CASES = STATIC_WORKFLOWS.parent / "research_cases"


def _ordered(frame: pd.DataFrame) -> pd.DataFrame:
    order = {key: i for i, key in enumerate(CITY_ORDER)}
    out = frame.copy()
    out["_ord"] = out["city"].map(order)
    return out.sort_values("_ord").drop(columns="_ord")


def _save(fig, dest: Path, name: str) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / name
    fig.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    STATIC_CASES.mkdir(parents=True, exist_ok=True)
    (STATIC_CASES / name).write_bytes(path.read_bytes())
    return path


def figure_annual_shr(annual: pd.DataFrame, dest: Path) -> Path:
    frame = _ordered(annual)
    colors = ["#b2182b" if v < 0 else "#2166ac" for v in frame["shr"]]
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    ax.bar(frame["short"], frame["shr"], color=colors, zorder=3)
    ax.axhline(0.0, color="0.2", linewidth=0.8)
    ax.set_ylabel("Annual SHR (supply − demand)")
    ax.set_title(
        "Streetscape heat resilience — eight-city application, not a validation"
    )
    ax.grid(axis="y", alpha=0.3, zorder=0)
    fig.text(
        0.5,
        0.01,
        "SHR uses Hong Kong JJA as a normative anchor. VATA ≠ UTCI ≠ SHR. "
        f"{CITATION}",
        ha="center",
        fontsize=8,
    )
    return _save(fig, dest, "hris_annual_shr.png")


def figure_monthly_heatmap(monthly: pd.DataFrame, dest: Path) -> Path:
    stats = load_city_stats()[["city", "short"]]
    frame = monthly.merge(stats, on="city", how="left")
    labels = [stats.set_index("city").loc[key, "short"] for key in CITY_ORDER]
    grid = (
        frame.pivot(index="city", columns="month", values="shr")
        .reindex(CITY_ORDER)
        .to_numpy(dtype=float)
    )
    vmax = float(np.nanmax(np.abs(grid)))
    fig, ax = plt.subplots(figsize=(10.4, 4.8))
    image = ax.imshow(grid, cmap="RdBu", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(12), labels=[str(m) for m in range(1, 13)])
    ax.set_yticks(range(len(labels)), labels=labels)
    ax.set_xlabel("Month")
    ax.set_title("Monthly SHR — hourly climatological proxy, not street-canyon UTCI")
    fig.colorbar(image, ax=ax, fraction=0.03, pad=0.02, label="SHR")
    fig.text(
        0.5,
        0.01,
        "Positive = city-mean VATA above the Hong Kong JJA benchmark. "
        f"Singapore n={SINGAPORE_N:,} (not TCIS {TCIS_SINGAPORE_N:,}).",
        ha="center",
        fontsize=8,
    )
    return _save(fig, dest, "hris_monthly_heatmap.png")


def figure_warming(annual: pd.DataFrame, dest: Path) -> Path:
    frame = _ordered(annual)
    x = np.arange(len(frame))
    width = 0.25
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    ax.bar(x - width, frame["shr"], width, label="present", color="#2166ac", zorder=3)
    ax.bar(x, frame["shr_plus15"], width, label="+1.5 °C", color="#ef8a62", zorder=3)
    ax.bar(x + width, frame["shr_plus25"], width, label="+2.5 °C", color="#b2182b", zorder=3)
    ax.axhline(0.0, color="0.2", linewidth=0.8)
    ax.set_xticks(x, frame["short"], rotation=20, ha="right")
    ax.set_ylabel("Annual SHR")
    ax.set_title("Warming bars — supply held fixed, demand recomputed")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.3, zorder=0)
    fig.text(
        0.5,
        0.01,
        "Air and open-sun MRT +1.5 / +2.5 °C. Not a design code and not medical advice.",
        ha="center",
        fontsize=8,
    )
    return _save(fig, dest, "hris_warming.png")


def _table_figure(frame: pd.DataFrame, title: str, dest: Path, name: str) -> Path:
    fig, ax = plt.subplots(figsize=(11.2, 0.55 * (len(frame) + 2)))
    ax.axis("off")
    table = ax.table(
        cellText=frame.astype(str).values,
        colLabels=list(frame.columns),
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.35)
    ax.set_title(title, fontsize=11, pad=12)
    fig.text(0.5, 0.02, CITATION, ha="center", fontsize=8)
    return _save(fig, dest, name)


def figure_robustness(sign: pd.DataFrame, dest: Path) -> Path:
    frame = _ordered(sign)[["short", "sign_stable", "always_surplus", "always_deficit", "min_shr", "max_shr"]]
    frame = frame.rename(
        columns={
            "short": "city",
            "sign_stable": "sign stable",
            "always_surplus": "always surplus",
            "always_deficit": "always deficit",
            "min_shr": "min SHR",
            "max_shr": "max SHR",
        }
    )
    for col in ("min SHR", "max SHR"):
        frame[col] = frame[col].map(lambda v: f"{float(v):.2f}")
    return _table_figure(
        frame,
        "Robustness sign stability across 18 variants — application, not validation",
        dest,
        "hris_robustness.png",
    )


def figure_domain(domain: pd.DataFrame, dest: Path) -> Path:
    stats = load_city_stats()
    frame = _ordered(domain.merge(stats[["city", "short"]], on="city", how="left"))
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    ax.bar(frame["short"], frame["frac_above_sg_pca95"], color="#4d4d4d", zorder=3)
    ax.set_ylabel("Fraction above Singapore PCA p95")
    ax.set_title("Domain shift relative to Singapore-trained TCIS features")
    ax.grid(axis="y", alpha=0.3, zorder=0)
    fig.text(
        0.5,
        0.01,
        "Johannesburg and Cape Town sit farthest above the Singapore envelope. "
        "This is a domain diagnostic, not a model ranking.",
        ha="center",
        fontsize=8,
    )
    return _save(fig, dest, "hris_domain_shift.png")


def main(out_dir: str | Path | None = None) -> dict:
    dest = Path(
        out_dir
        or ROOT / "examples" / "output" / "research_cases" / "heat_resilience_in_sight"
    )
    dest.mkdir(parents=True, exist_ok=True)
    calibration = load_calibration()
    stats = load_city_stats()
    annual = load_annual()
    monthly = load_monthly()
    sign = load_sign_stability()
    domain = load_domain_shift()
    sg_n = int(stats.loc[stats["city"] == "svi_sg", "n"].iloc[0])
    if sg_n != SINGAPORE_N:
        raise RuntimeError(f"HRIS Singapore n={sg_n}, expected {SINGAPORE_N}")
    if abs(float(calibration["d_ref"]) - D_REF) > 0.001:
        raise RuntimeError("Hong Kong JJA d_ref drifted from 7.991")
    figures = [
        figure_annual_shr(annual, dest),
        figure_monthly_heatmap(monthly, dest),
        figure_warming(annual, dest),
        figure_robustness(sign, dest),
        figure_domain(domain, dest),
    ]
    provenance = dest / "provenance.json"
    provenance.write_text(
        json.dumps(
            {
                "case": "heat_resilience_in_sight",
                "role": "eight-city application, not a validation",
                "singapore_n": sg_n,
                "tcis_singapore_n": TCIS_SINGAPORE_N,
                "v_ref": float(calibration["v_ref"]),
                "d_ref": float(calibration["d_ref"]),
                "cache_version": calibration.get("cache_version"),
                "citation": CITATION,
                "figures": [str(path) for path in figures],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "summary": (
            f"HRIS application n_sg={sg_n} (not TCIS {TCIS_SINGAPORE_N}); "
            f"d_ref={float(calibration['d_ref']):.3f}"
        ),
        "figures": figures,
        "calibration": calibration,
        "manifest": load_manifest(),
        "v_ref": V_REF,
        "d_ref": D_REF,
    }


if __name__ == "__main__":
    result = main()
    print(result["summary"])
    for path in result["figures"]:
        print(path)
