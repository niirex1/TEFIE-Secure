"""Load and summarise the fetched ESC/VSC graph data (TU text format).

Run `python datasets/fetch_dataset.py` first to download the data, then this
script reports dataset statistics a reviewer can check against the manuscript
and the source paper: graph count, label distribution, node/edge counts, and
feature dimension. It performs no model inference and fabricates no predictions;
it only demonstrates that the real data is present and parseable.

What these files are: the contract-level graph datasets released with DR-GCN
(REENTRANCY_CORENODES_1671, LOOP_CORENODES_1317), i.e. the processed graphs the
GNN baselines (TMP, CGE, DR-GCN) train on. They are a curated view of the ESC
and VSC corpora of Zhuang et al. (IJCAI 2020). The full function-level ESC
(~307k functions) and VSC (~13.7k functions) are at
https://github.com/Messi-Q/Smart-Contract-Dataset .
"""
from __future__ import annotations
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
PREFIX = "SMARTCONTRACT_full_"

# task -> (source folder used by fetch_dataset.py, vulnerability, corpus)
TASKS = {
    "reentrancy": ("reentrancy", "reentrancy", "ESC"),
    "loops": ("loops", "infinite loop", "VSC"),
}


def _read_lines(path):
    with open(path) as f:
        return [ln.strip() for ln in f if ln.strip() != ""]


def summarise(task: str) -> dict | None:
    folder, vuln, corpus = TASKS[task]
    base = os.path.join(RAW, folder)
    labels_p = os.path.join(base, PREFIX + "graph_labels.txt")
    if not os.path.exists(labels_p):
        print(f"[{task}] not downloaded yet — run: python datasets/fetch_dataset.py --task {task}")
        return None
    labels = [int(x) for x in _read_lines(labels_p)]
    indicator = [int(x) for x in _read_lines(os.path.join(base, PREFIX + "graph_indicator.txt"))]
    edges = _read_lines(os.path.join(base, PREFIX + "A.txt"))
    attr_p = os.path.join(base, PREFIX + "node_attributes.txt")
    feat_dim = None
    if os.path.exists(attr_p):
        with open(attr_p) as f:
            feat_dim = len(f.readline().split(","))
    pos = sum(1 for v in labels if v == 1)
    info = {
        "task": task, "vulnerability": vuln, "corpus": corpus,
        "graphs": len(labels), "positive": pos, "negative": len(labels) - pos,
        "positive_rate_pct": round(100 * pos / len(labels), 1) if labels else 0.0,
        "nodes": len(indicator), "edges": len(edges), "feature_dim": feat_dim,
    }
    print(f"[{task}] {corpus} / {vuln}")
    print(f"   graphs        : {info['graphs']}")
    print(f"   label balance : {info['positive']} vulnerable / {info['negative']} benign "
          f"({info['positive_rate_pct']}% positive)")
    print(f"   nodes         : {info['nodes']}")
    print(f"   edges         : {info['edges']}")
    print(f"   node feat dim : {info['feature_dim']}")
    return info


def list_synthetic():
    d = os.path.join(HERE, "synthetic_contracts")
    sols = sorted(f for f in os.listdir(d) if f.endswith(".sol")) if os.path.isdir(d) else []
    print("\nOffline synthetic examples (SYNTHETIC — not ESC/VSC):")
    for s in sols:
        print(f"   {s}")


def main():
    print("ESC/VSC graph data summary\n")
    any_loaded = False
    for t in TASKS:
        if summarise(t) is not None:
            any_loaded = True
        print()
    list_synthetic()
    if not any_loaded:
        print("\nNo real data found. Run `python datasets/fetch_dataset.py` to download it.")
    print("\nNote: producing TEFIE-Secure predictions on these graphs requires the "
          "detection model (released with the artifact). The metric pipeline in "
          "src/ then consumes those predictions; see data/SCHEMA.md.")


if __name__ == "__main__":
    main()
