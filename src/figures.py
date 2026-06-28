"""Regenerate the paper's figures from raw inputs in data/.

Figures produced (written to outputs/):
  - reentrancy-ROC.pdf, timestamp-ROC.pdf, loops-ROC.pdf : per-task ROC with
    per-model AUC in the legend and the two static tools as single (FPR, TPR)
    points, matching the layout of the figures shipped in paper_figures/.
  - feature-importance.pdf : mean |SHAP| per feature group, grouped by task.

Curves and AUCs are computed from data/predictions_classification.csv via
src/metrics.roc_curve; the static-tool points and SHAP magnitudes are read from
data/static_points.csv and data/shap.csv. Nothing is hardcoded from the paper.
"""
from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from metrics import roc_curve

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
OUT = os.path.join(os.path.dirname(__file__), "..", "outputs")

# Per task, which learned models to draw as curves (in legend order).
ROC_MODELS = {
    "reentrancy": ["TEFIE-Secure", "VDM-AEI", "FELLMVP", "SmartGuard"],
    "timestamp": ["TEFIE-Secure", "VDM-AEI", "FELLMVP", "SmartGuard"],
    "loops": ["TEFIE-Secure", "FELLMVP", "SmartGuard", "SCVulBERT"],
}


def _roc_for_task(task: str, preds: pd.DataFrame, static: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(3.2, 3.0))
    sub = preds[preds["task"] == task]
    for model in ROC_MODELS.get(task, sorted(sub["model"].unique())):
        g = sub[sub["model"] == model]
        if g.empty:
            continue
        fpr, tpr, auc = roc_curve(g["y_true"], g["y_score"])
        ax.plot(fpr, tpr, lw=1.4, label=f"{model} ({auc:.2f})")
    for _, r in static[static["task"] == task].iterrows():
        ax.plot(r["fpr"], r["tpr"], marker="o", ms=5, ls="",
                label=f'{r["tool"]} ({r["fpr"]:.3f}, {r["tpr"]:.3f})')
    ax.plot([0, 1], [0, 1], color="0.7", lw=0.8, ls="--")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel("FPR"); ax.set_ylabel("TPR")
    ax.legend(fontsize=6, loc="lower right", frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"{task}-ROC.pdf"))
    plt.close(fig)


def roc_figures():
    preds = pd.read_csv(os.path.join(DATA, "predictions_classification.csv"))
    static = pd.read_csv(os.path.join(DATA, "static_points.csv"))
    for task in ["reentrancy", "timestamp", "loops"]:
        _roc_for_task(task, preds, static)


def shap_figure():
    df = pd.read_csv(os.path.join(DATA, "shap.csv"))
    groups = ["call-edge", "state-update", "loop-structure", "block-variable", "normalization"]
    tasks = ["Reentrancy", "Timestamp", "Loops"]
    piv = df.pivot(index="feature_group", columns="task", values="mean_abs_shap").reindex(groups)
    x = np.arange(len(groups)); w = 0.25
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    for i, t in enumerate(tasks):
        ax.bar(x + (i - 1) * w, piv[t].values, w, label=t)
    ax.set_xticks(x); ax.set_xticklabels(groups, rotation=20, ha="right", fontsize=7)
    ax.set_xlabel("Feature group"); ax.set_ylabel("mean |SHAP|")
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "feature-importance.pdf"))
    plt.close(fig)


def build_all():
    os.makedirs(OUT, exist_ok=True)
    roc_figures(); shap_figure()


if __name__ == "__main__":
    build_all()
    print("figures written to outputs/")
