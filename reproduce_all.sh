#!/usr/bin/env bash
# Reproduce every table and figure reported in the main text of
# "TEFIE-Secure: Propagation-Time Screening of Smart Contract Vulnerabilities".
#
# This script is the entry point referenced in Appendix B of the manuscript.
# It is idempotent: re-running rebuilds outputs in graph/output/.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRAPH_DIR="${ROOT_DIR}/graph"

if [[ ! -d "${GRAPH_DIR}" ]]; then
  echo "error: graph/ directory not found in ${ROOT_DIR}" >&2
  exit 1
fi

cd "${GRAPH_DIR}"

# Optional virtual environment (default: install into current Python).
if [[ "${TEFIE_USE_VENV:-1}" -eq 1 ]]; then
  if [[ ! -d ".venv" ]]; then
    echo "[1/3] creating virtual environment in ${GRAPH_DIR}/.venv ..."
    python3 -m venv .venv
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

echo "[2/3] installing pinned dependencies ..."
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet -r requirements.txt

echo "[3/3] regenerating tables and figures ..."
make paper

echo
echo "Done. Outputs are in ${GRAPH_DIR}/output:"
echo "  tables: $(ls "${GRAPH_DIR}/output/tables" | wc -l) files"
echo "  figs:   $(ls "${GRAPH_DIR}/output/figs"   | wc -l) files"
echo "  eval:   $(ls "${GRAPH_DIR}/output/eval"   | wc -l) files"
