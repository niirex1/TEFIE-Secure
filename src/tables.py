"""Build the paper's result tables from raw inputs in data/.

Tables produced (written to outputs/ as CSV):
  - table_accuracy.csv   : per-task F1/precision/recall/FPR/FNR per model (default threshold)
  - table_ablation.csv   : per-task F1 per ablation variant
  - table_runtime.csv    : per-model latency / throughput / memory / parameters
  - table_realworld.csv  : RQ5 post-2023 mainnet detection and weak-negative precision

The accuracy and ablation tables are derived from per-instance predictions via
src/metrics.py; the runtime table is a tabulation of measured timings; the
real-world table is computed from RQ5 predictions and disclosure labels. No
value here is hardcoded from the manuscript.
"""
from __future__ import annotations
import os
import pandas as pd
import numpy as np
from metrics import confusion_at_threshold, metrics_from_counts, select_threshold

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
OUT = os.path.join(os.path.dirname(__file__), "..", "outputs")


def _counts_table(pred_csv: str) -> pd.DataFrame:
    """Reduce per-instance predictions to per-(task, model) confusion counts and metrics."""
    df = pd.read_csv(pred_csv)
    rows = []
    for (task, model), g in df.groupby(["task", "model"]):
        thr = select_threshold(g["y_true"], g["y_score"], "default")
        c = confusion_at_threshold(g["y_true"], g["y_score"], thr)
        m = metrics_from_counts(c)
        rows.append({"task": task, "model": model, "threshold": round(thr, 4),
                     **c, **{k: round(v, 2) for k, v in m.items()}})
    return pd.DataFrame(rows)


def accuracy_table() -> pd.DataFrame:
    df = _counts_table(os.path.join(DATA, "predictions_classification.csv"))
    df.to_csv(os.path.join(OUT, "table_accuracy.csv"), index=False)
    return df


def ablation_table() -> pd.DataFrame:
    src = pd.read_csv(os.path.join(DATA, "predictions_ablation.csv"))
    rows = []
    for (task, variant), g in src.groupby(["task", "variant"]):
        thr = select_threshold(g["y_true"], g["y_score"], "default")
        m = metrics_from_counts(confusion_at_threshold(g["y_true"], g["y_score"], thr))
        rows.append({"task": task, "variant": variant, "f1": round(m["f1"], 2)})
    tab = pd.DataFrame(rows).pivot(index="variant", columns="task", values="f1").reset_index()
    tab.to_csv(os.path.join(OUT, "table_ablation.csv"), index=False)
    return tab


def runtime_table() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA, "runtime.csv"))
    df.to_csv(os.path.join(OUT, "table_runtime.csv"), index=False)
    return df


def realworld_table() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA, "realworld.csv"))
    thr = select_threshold(df["y_true"], df["y_score"], "high_recall", target=0.02)
    df = df.assign(flagged=(df["y_score"] >= thr).astype(int))
    disclosed = df[df["disclosed"] == 1]
    by_type = (disclosed.groupby("vuln_type")
               .agg(disclosed=("y_true", "size"), flagged=("flagged", "sum"))
               .reset_index())
    by_type["recall_pct"] = (100 * by_type["flagged"] / by_type["disclosed"]).round(1)
    # weak-negative precision: positives = disclosed-and-flagged; negatives = undisclosed-but-flagged
    tp = int(disclosed["flagged"].sum())
    fp_weak = int(df[(df["disclosed"] == 0) & (df["flagged"] == 1)].shape[0])
    precision_weak = round(100 * tp / (tp + fp_weak), 1) if (tp + fp_weak) else 0.0
    summary = pd.DataFrame([{
        "threshold_mode": "high_recall(FNR<=2%)", "threshold": round(thr, 4),
        "disclosed_total": int(disclosed.shape[0]), "disclosed_flagged": tp,
        "weak_negative_flags": fp_weak, "weak_negative_precision_pct": precision_weak,
    }])
    by_type.to_csv(os.path.join(OUT, "table_realworld_bytype.csv"), index=False)
    summary.to_csv(os.path.join(OUT, "table_realworld_summary.csv"), index=False)
    return summary


def build_all():
    os.makedirs(OUT, exist_ok=True)
    accuracy_table(); ablation_table(); runtime_table(); realworld_table()


if __name__ == "__main__":
    build_all()
    print("tables written to outputs/")
