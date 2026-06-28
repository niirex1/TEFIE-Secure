# Datasets (ESC / VSC)

The manuscript evaluates on two public corpora introduced by Zhuang et al.:

> Yuan Zhuang, Zhenguang Liu, Peng Qian, Qi Liu, Xiang Wang, Qinming He.
> *Smart Contract Vulnerability Detection using Graph Neural Network.*
> IJCAI 2020, pp. 3283–3290.

```bibtex
@inproceedings{zhuang2020smart,
  title     = {Smart Contract Vulnerability Detection using Graph Neural Network},
  author    = {Zhuang, Yuan and Liu, Zhenguang and Qian, Peng and Liu, Qi and Wang, Xiang and He, Qinming},
  booktitle = {IJCAI},
  pages     = {3283--3290},
  year      = {2020}
}
```

| corpus | contracts | functions | tasks (this paper)              |
|--------|-----------|-----------|---------------------------------|
| ESC    | 40,932    | ~307,396  | reentrancy, timestamp dependence|
| VSC    | 4,170     | ~13,761   | infinite loop                   |

These counts are the authors' published figures and match the manuscript.

## This artifact does not redistribute the data

Both source repositories carry **no explicit licence**, so the right to
redistribute their files is unclear. Rather than bundle third-party data of
uncertain licence into this artifact, `fetch_dataset.py` downloads the authentic
files **directly from the authors' repository**, pinned to an immutable commit,
and verifies each one against a recorded SHA-256 (size for the large feature
files). Reviewers therefore obtain exactly what the authors published. **Please
cite Zhuang et al. (2020) when using this data.**

## Sources

- **Dataset home (full ESC/VSC, raw contracts, instructions):**
  https://github.com/Messi-Q/Smart-Contract-Dataset
- **Ready-to-use graph data fetched by the script** (DR-GCN release):
  https://github.com/Messi-Q/GraphDeeSmartContract
  pinned commit `1709aa5807bdf5ca20dd1be5d003c62ebdaf05dd`,
  under `training_data/`.

### What the fetch script retrieves

`fetch_dataset.py` downloads the **contract-level graph datasets** the GNN
baselines (TMP, CGE, DR-GCN) train on:

- `REENTRANCY_CORENODES_1671` — reentrancy graphs (ESC view)
- `LOOP_CORENODES_1317` — infinite-loop graphs (VSC view)

Each is in TU / graph-classification text format (`_A.txt` edge list,
`_graph_indicator.txt`, `_graph_labels.txt`, `_node_labels.txt`,
`_node_attributes.txt`). These are a **curated, contract-level view** of ESC/VSC,
not the full function-level corpora — use them for a runnable demo. The complete
function-level ESC (including the timestamp-dependence split, which is not part
of the DR-GCN release) is at the dataset-home repository above.

## How to obtain the data

```bash
python datasets/fetch_dataset.py          # reentrancy (ESC) + loops (VSC)
python datasets/load_dataset.py           # print verifiable dataset statistics
```

`load_dataset.py` reports graph counts, label balance, node/edge counts, and
feature dimension so the data can be checked against the paper and the source.

## Offline demo without a download

`synthetic_contracts/` holds three **synthetic, hand-authored** Solidity files
(one per task) for an offline demo. They are clearly labelled and reproduce no
third-party data; see `synthetic_contracts/README.md`.

## Scope note

These corpora are the **inputs** to the detector. Turning contracts/graphs into
predictions requires the TEFIE-Secure model (released with the artifact); the
metric pipeline in `src/` then consumes those predictions (`data/SCHEMA.md`).
This artifact does not ship model predictions for the real data, and does not
fabricate any.
