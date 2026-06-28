#!/usr/bin/env bash
# Reproduce every data-derived table and figure in the TEFIE-Secure manuscript.
#
# This rebuilds outputs from the contents of data/. With the SYNTHETIC smoke-test
# data shipped here it produces well-formed but non-paper results; point data/ at
# your real experimental outputs (data/SCHEMA.md) to reproduce the manuscript.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT}"

echo "[1/2] installing dependencies ..."
python3 -m pip install --quiet -r requirements.txt

echo "[2/2] building tables, figures, workbook ..."
python3 reproduce.py --synth      # use existing data/: drop the --synth flag

echo
echo "Outputs in ${ROOT}/outputs:"
echo "  tables : table_accuracy.csv (Table II), table_runtime.csv (Table III),"
echo "           table_ablation.csv (Table IV), table_realworld_*.csv (Table V)"
echo "  figures: reentrancy/timestamp/loops-ROC.pdf (Fig 2), feature-importance.pdf"
echo "  excel  : results.xlsx (metrics as in-cell formulas over the counts)"
