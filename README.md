# TEFIE-Secure

This repository contains the artifact for the TEFIE-Secure paper.

## Reproducing paper tables and figures

### Prerequisites

- Python 3.9+

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r graph/requirements.txt
```

### Generate tables and figures

```bash
cd graph
make paper
```

## Outputs

### Tables

- graph/output/tables/table1.csv
- graph/output/tables/table1.tex
- graph/output/tables/table2.csv
- graph/output/tables/table2.tex
- graph/output/tables/table3.csv
- graph/output/tables/table3.tex
- graph/output/tables/table4.csv
- graph/output/tables/table4.tex

### Figures

- graph/output/figs/fig3_roc.png
- graph/output/figs/fig3_roc.pdf
- graph/output/figs/fig4_shap.png
- graph/output/figs/fig4_shap.pdf

## Repository layout

- graph/: reproduction entry point (scripts, assets, and outputs)
- paper/assets/: the paper PDF and the spreadsheet inputs used to regenerate figures
- paper/figs/: reference images used in the manuscript
- access_control/, reentrancy/, time_manipulation/, ...: Solidity samples grouped by vulnerability family
