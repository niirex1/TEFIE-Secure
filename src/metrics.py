"""Core metric functions for the TEFIE-Secure artifact.

Every metric is computed from raw per-instance predictions (y_true, y_score).
Nothing in this file hardcodes a result reported in the paper; the numbers a run
produces come entirely from the contents of data/. Replace the synthetic
smoke-test data in data/ with your real experimental outputs to reproduce the
values in the manuscript.
"""
from __future__ import annotations
import numpy as np


def confusion_at_threshold(y_true: np.ndarray, y_score: np.ndarray, thr: float) -> dict:
    """Confusion-matrix counts at a decision threshold.

    Positive class is 1. A score >= thr is predicted positive.
    """
    y_true = np.asarray(y_true).astype(int)
    y_pred = (np.asarray(y_score) >= thr).astype(int)
    tp = int(np.sum((y_pred == 1) & (y_true == 1)))
    fp = int(np.sum((y_pred == 1) & (y_true == 0)))
    fn = int(np.sum((y_pred == 0) & (y_true == 1)))
    tn = int(np.sum((y_pred == 0) & (y_true == 0)))
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def metrics_from_counts(c: dict) -> dict:
    """Derive F1/precision/recall/FPR/FNR (in %) from confusion counts.

    These are the same formulas the results workbook applies in-cell, so the
    spreadsheet and this module agree by construction.
    """
    tp, fp, fn, tn = c["tp"], c["fp"], c["fn"], c["tn"]
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    fnr = fn / (fn + tp) if (fn + tp) else 0.0
    return {
        "precision": 100.0 * precision,
        "recall": 100.0 * recall,
        "f1": 100.0 * f1,
        "fpr": 100.0 * fpr,
        "fnr": 100.0 * fnr,
    }


def roc_curve(y_true: np.ndarray, y_score: np.ndarray):
    """ROC curve (fpr, tpr arrays) and AUC, computed by score-threshold sweep.

    Pure-numpy implementation so the artifact has no scikit-learn dependency for
    the figures; results match sklearn.metrics.roc_curve / roc_auc_score.
    """
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score, dtype=float)
    order = np.argsort(-y_score)
    y_true = y_true[order]
    y_score = y_score[order]
    distinct = np.where(np.diff(y_score))[0]
    threshold_idx = np.r_[distinct, y_true.size - 1]
    tps = np.cumsum(y_true)[threshold_idx]
    fps = 1 + threshold_idx - tps
    tps = np.r_[0, tps]
    fps = np.r_[0, fps]
    P = tps[-1] if tps[-1] > 0 else 1
    N = fps[-1] if fps[-1] > 0 else 1
    tpr = tps / P
    fpr = fps / N
    _trapz = getattr(np, "trapezoid", getattr(np, "trapz", None))
    auc = float(_trapz(tpr, fpr))
    return fpr, tpr, auc


def select_threshold(y_true, y_score, mode: str = "default", target: float | None = None) -> float:
    """Pick an operating threshold.

    mode='default'   : threshold maximizing F1 on the provided data.
    mode='high_recall': smallest threshold with FNR <= target (e.g. 0.02).
    mode='high_prec'  : largest threshold with FPR <= target (e.g. 0.005).
    """
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score, dtype=float)
    cand = np.unique(y_score)
    if mode == "default":
        best_thr, best_f1 = 0.5, -1.0
        for t in cand:
            m = metrics_from_counts(confusion_at_threshold(y_true, y_score, t))
            if m["f1"] > best_f1:
                best_f1, best_thr = m["f1"], float(t)
        return best_thr
    if mode == "high_recall":
        target = 0.02 if target is None else target
        ok = [float(t) for t in cand
              if metrics_from_counts(confusion_at_threshold(y_true, y_score, t))["fnr"] <= 100 * target]
        return min(ok) if ok else float(cand.min())
    if mode == "high_prec":
        target = 0.005 if target is None else target
        ok = [float(t) for t in cand
              if metrics_from_counts(confusion_at_threshold(y_true, y_score, t))["fpr"] <= 100 * target]
        return max(ok) if ok else float(cand.max())
    raise ValueError(f"unknown mode: {mode}")
