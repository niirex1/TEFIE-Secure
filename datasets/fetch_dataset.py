"""Fetch the real ESC/VSC evaluation data from its authoritative public source.

Source : Messi-Q/GraphDeeSmartContract (the DR-GCN release of the Zhuang et al.
         IJCAI-2020 datasets), pinned to an immutable commit for reproducibility.
Dataset: Zhuang, Liu, Qian, Liu, Wang, He. "Smart Contract Vulnerability
         Detection using Graph Neural Network." IJCAI 2020, pp. 3283-3290.

We deliberately do NOT redistribute this third-party data inside the artifact:
the source repositories carry no explicit licence, so the right to redistribute
is unclear. This script pulls the authentic files directly from the authors'
repository so reviewers obtain exactly the data the authors published, and
verifies every file against a recorded SHA-256 (and size for the large feature
files). Please cite the authors above when you use this data.

The files use the TU / graph-classification text format:
  *_A.txt                edge list (one "row, col" per line)
  *_graph_indicator.txt  graph id for each node
  *_graph_labels.txt     one label per graph (the supervision signal)
  *_node_labels.txt      node type id for each node
  *_node_attributes.txt  node feature vector for each node

Usage:
  python datasets/fetch_dataset.py            # fetch reentrancy (ESC) + loops (VSC)
  python datasets/fetch_dataset.py --task reentrancy
"""
from __future__ import annotations
import argparse
import hashlib
import os
import sys
import urllib.request

REPO = "Messi-Q/GraphDeeSmartContract"
COMMIT = "1709aa5807bdf5ca20dd1be5d003c62ebdaf05dd"  # pinned; verified provenance
RAW = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/training_data"
HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(HERE, "raw")

# Verified SHA-256 for the small files; size (bytes) for the large feature files.
# task -> source-folder -> {filename: {"sha256": ...} | {"size": ...}}
MANIFEST = {
    "reentrancy": ("REENTRANCY_CORENODES_1671", {
        "SMARTCONTRACT_full_graph_labels.txt":    {"sha256": "feb420d97f3faba4355ae84296d36c3635b86a7b4dc8e9980a40130598374821"},
        "SMARTCONTRACT_full_graph_indicator.txt": {"sha256": "1437d5552aa777ed7b8a6545f949b870dfd227fa601ca602077813c77ecb5089"},
        "SMARTCONTRACT_full_A.txt":               {"sha256": "dbe8e984f316f0758c153ed2f650d2fd8af57bc7b9453db5bfc7727bca98074e"},
        "SMARTCONTRACT_full_node_labels.txt":     {"sha256": "cb9b6f50cfd04e4351d3334c2056824ee298da48eb5d172380c2870cafd4255b"},
        "SMARTCONTRACT_full_node_attributes.txt": {"size": 7340372},
    }),
    "loops": ("LOOP_CORENODES_1317", {
        "SMARTCONTRACT_full_graph_labels.txt":    {"sha256": "f4ec16ae9d3a1db98cdbf01a5aad2ecc1ebcd49c668741ebbd900f70dea77cc1"},
        "SMARTCONTRACT_full_graph_indicator.txt": {"sha256": "59b8687fc56d68260d95d541e56341502b6a3c32971c813681fb5516cb13d1b2"},
        "SMARTCONTRACT_full_A.txt":               {"sha256": "4007c52e123140a9dc09ba3641f17760fa720df415a6f968185e5be5f52fd57d"},
        "SMARTCONTRACT_full_node_labels.txt":     {"sha256": "3522b57ab587333320509122313d2464ba044a5c537e11f0327216ad1f4b4792"},
        "SMARTCONTRACT_full_node_attributes.txt": {"size": 3849417},
    }),
}

# Timestamp-dependence graphs are not part of the DR-GCN release; obtain the full
# ESC (which includes timestamp) from the authors' continuously-updated home:
TIMESTAMP_NOTE = ("Messi-Q/Smart-Contract-Dataset "
                  "(https://github.com/Messi-Q/Smart-Contract-Dataset)")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(url: str, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as r, open(path, "wb") as out:
        out.write(r.read())


def _verify(path: str, spec: dict) -> bool:
    if "sha256" in spec:
        got = _sha256(path)
        ok = got == spec["sha256"]
        print(f"      sha256 {'OK' if ok else 'MISMATCH'}: {got[:16]}...")
        return ok
    size = os.path.getsize(path)
    ok = size == spec["size"]
    print(f"      size {'OK' if ok else 'MISMATCH'}: {size} (expected {spec['size']})")
    return ok


def fetch_task(task: str) -> bool:
    folder, files = MANIFEST[task]
    print(f"[{task}] from {REPO}@{COMMIT[:10]} / {folder}")
    all_ok = True
    for fname, spec in files.items():
        url = f"{RAW}/{folder}/{fname}"
        out = os.path.join(DEST, task, fname)
        print(f"  - {fname}")
        try:
            _download(url, out)
        except Exception as e:  # network disabled / blocked / offline
            print(f"      DOWNLOAD FAILED: {e}")
            all_ok = False
            continue
        all_ok &= _verify(out, spec)
    return all_ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=list(MANIFEST) + ["all"], default="all")
    args = ap.parse_args()
    tasks = list(MANIFEST) if args.task == "all" else [args.task]
    print(f"Destination: {DEST}\n")
    results = {t: fetch_task(t) for t in tasks}
    print("\nSummary:")
    for t, ok in results.items():
        print(f"  {t}: {'verified' if ok else 'INCOMPLETE (see messages above)'}")
    print(f"\nTimestamp-dependence (ESC) is published separately at {TIMESTAMP_NOTE}.")
    if not all(results.values()):
        print("\nIf downloads failed, your environment may block network access; "
              "fetch the files manually from the URLs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
