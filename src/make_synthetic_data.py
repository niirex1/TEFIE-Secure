"""Generate SYNTHETIC smoke-test data so the pipeline runs end-to-end.

  ###  THIS DATA IS SYNTHETIC AND DOES NOT REPRODUCE THE PAPER'S RESULTS.  ###

It exists only to demonstrate that the reproduction scripts execute and produce
well-formed tables, figures, and a workbook. The scores are drawn from generic
class-separated distributions with arbitrary parameters; they are not calibrated
to any value reported in the manuscript. To reproduce the paper's tables and
figures, delete the files in data/ and replace them with your real experimental
outputs following data/SCHEMA.md.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
RNG = np.random.default_rng(0)

TASKS = ["reentrancy", "timestamp", "loops"]
MODELS = ["TEFIE-Secure", "VDM-AEI", "FELLMVP", "SmartGuard", "SCVulBERT"]
ABLATION = ["full", "w/o cross-addr. typing", "w/o feature selection",
            "w/o contextual embeddings", "w/o preprocessing", "w/o residual refiner"]
SEEDS = [0, 1, 2, 3, 4]
N_PER = 400  # small smoke-test set


def _scored(n_pos, n_neg, sep):
    """Return (y_true, y_score) with arbitrary class separation `sep`."""
    pos = RNG.normal(sep, 1.0, n_pos)
    neg = RNG.normal(0.0, 1.0, n_neg)
    s = np.concatenate([pos, neg])
    s = 1 / (1 + np.exp(-s))  # squash to (0,1)
    y = np.concatenate([np.ones(n_pos), np.zeros(n_neg)]).astype(int)
    return y, s


def predictions_classification():
    rows = []
    for task in TASKS:
        for model in MODELS:
            for seed in SEEDS:
                sep = RNG.uniform(2.0, 3.2)  # arbitrary, NOT tuned to paper AUCs
                y, s = _scored(N_PER // 2, N_PER // 2, sep)
                for i, (yt, ys) in enumerate(zip(y, s)):
                    rows.append((task, model, seed, i, int(yt), round(float(ys), 4)))
    pd.DataFrame(rows, columns=["task", "model", "seed", "instance_id", "y_true", "y_score"]) \
        .to_csv(os.path.join(DATA, "predictions_classification.csv"), index=False)


def predictions_ablation():
    rows = []
    for task in TASKS:
        for variant in ABLATION:
            for seed in SEEDS:
                sep = RNG.uniform(1.4, 3.0)
                y, s = _scored(N_PER // 2, N_PER // 2, sep)
                for i, (yt, ys) in enumerate(zip(y, s)):
                    rows.append((task, variant, seed, i, int(yt), round(float(ys), 4)))
    pd.DataFrame(rows, columns=["task", "variant", "seed", "instance_id", "y_true", "y_score"]) \
        .to_csv(os.path.join(DATA, "predictions_ablation.csv"), index=False)


def runtime():
    rows = []
    for model in MODELS + ["Slither", "Mythril"]:
        rows.append({
            "model": model, "mode": "source",
            "latency_ms_p50": round(RNG.uniform(10, 220), 1),
            "latency_ms_p99": round(RNG.uniform(30, 260), 1),
            "throughput_inst_s": round(RNG.uniform(5, 100), 1),
            "peak_vram_gb": round(RNG.uniform(0.5, 6.0), 1),
            "params_m": round(RNG.uniform(1.0, 350.0), 1),
        })
    pd.DataFrame(rows).to_csv(os.path.join(DATA, "runtime.csv"), index=False)


def static_points():
    rows = []
    for task in TASKS:
        for tool in ["Slither", "Mythril"]:
            rows.append({"task": task, "tool": tool,
                         "fpr": round(RNG.uniform(0.03, 0.1), 3),
                         "tpr": round(RNG.uniform(0.5, 0.8), 3)})
    pd.DataFrame(rows).to_csv(os.path.join(DATA, "static_points.csv"), index=False)


def shap():
    groups = ["call-edge", "state-update", "loop-structure", "block-variable", "normalization"]
    rows = []
    for task in ["Reentrancy", "Timestamp", "Loops"]:
        for grp in groups:
            rows.append({"task": task, "feature_group": grp,
                         "mean_abs_shap": round(RNG.uniform(0.02, 0.6), 3)})
    pd.DataFrame(rows).to_csv(os.path.join(DATA, "shap.csv"), index=False)


def realworld():
    types = ["reentrancy", "timestamp", "loops", "access-control", "bridge"]
    rows = []
    for cid in range(1500):
        disclosed = int(RNG.random() < 0.032)
        vt = RNG.choice(types)
        sep = 2.6 if disclosed else 0.4
        y = disclosed
        score = 1 / (1 + np.exp(-RNG.normal(sep if y else 0.0, 1.0)))
        rows.append({"contract_id": f"0x{cid:040x}", "vuln_type": vt,
                     "y_true": y, "y_score": round(float(score), 4), "disclosed": disclosed})
    pd.DataFrame(rows).to_csv(os.path.join(DATA, "realworld.csv"), index=False)


def build_all():
    os.makedirs(DATA, exist_ok=True)
    predictions_classification(); predictions_ablation(); runtime()
    static_points(); shap(); realworld()


if __name__ == "__main__":
    build_all()
    print("SYNTHETIC smoke-test data written to data/ (does NOT reproduce paper values)")
