# Revision notes

This package is the revised reproduction artifact for TEFIE-Secure. It replaces a
prior version whose reproduction harness did not compute results. The changes:

## Removed

- **`graph/scripts/make_paper_tables_figs.py`** — the previous "reproduction"
  script. It opened the paper PDF (`--paper paper/assets/tefie_secure_paper.pdf`)
  and regex-extracted the reported numbers (`parse_table1..4`), then wrote them
  back out as `table*.csv/tex`. It computed nothing; it copied the paper's own
  numbers, so the tables matched the paper by construction.
- **`graph/paper/assets/*_Exact.xlsx`** — hand-authored spreadsheets containing
  idealised ROC/SHAP curves (e.g. a `Proposed_TPR` column with round values).
  The figures were replotted from these, not computed from model scores.
- **The pre-generated `graph/output/` tables and figures** — outputs of the two
  steps above.
- **The `*.R` reference files** — these are disconnected skeletons (they read no
  data, use `runif()` placeholders for embeddings, fit and predict on the same
  matrix with no train/test split) and, critically, build a full ImageNet
  ResNet-50 (`application_resnet50(weights="imagenet")`), which contradicts the
  manuscript's "reduced-width ... not the 25 M-parameter ImageNet instantiation,
  ... 1.2 M parameters." They do not produce the paper's results and should not
  ship as if they did. If you want to include the real implementation, add the
  code that actually produced the reported numbers.

## Added (the honest pipeline)

- `reproduce.py`, `src/` — compute every data-derived table and figure from raw
  per-instance predictions and measurements (`src/metrics.py`, `tables.py`,
  `figures.py`, `workbook.py`). Nothing is hardcoded from the manuscript.
- `data/` + `data/SCHEMA.md` — the input schema, shipped with clearly-labelled
  SYNTHETIC smoke-test data so the pipeline runs end-to-end.
- `datasets/` — verified provenance for ESC/VSC (Zhuang et al., IJCAI 2020), a
  checksum-verified fetch script that pulls the authentic data from the authors'
  repository, and synthetic example contracts for an offline demo.
- `paper_figures/` — your ROC/SHAP figures and the Fig 1/2 diagrams, for
  reference.

## What you still have to do to reproduce the manuscript

The reported numbers are not in this artifact because they were not measured by
anything in the artifact (the manuscript itself still marks the residual-refiner
row provisional and the bytecode-mode result a run-or-report item). To reproduce
them: run your real implementation on the real ESC/VSC data, write the resulting
predictions/timings/SHAP values into `data/` per `data/SCHEMA.md`, run
`./reproduce_all.sh`, and update the manuscript's provisional values to match
what the run produces.
