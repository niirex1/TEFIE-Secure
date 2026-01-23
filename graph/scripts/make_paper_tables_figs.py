#!/usr/bin/env python3
"""Generate TEFIE-Secure paper tables and figures.

Run from `graph/`:
  python3 scripts/make_paper_tables_figs.py --paper paper/assets/tefie_secure_paper.pdf --assets paper/assets --out output

Outputs
  Tables: output/tables/table{1..4}.csv and output/tables/table{1..4}.tex
  Figures: output/figs/fig3_roc.(png|pdf) and output/figs/fig4_shap.(png|pdf)
"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from pypdf import PdfReader

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


@dataclass(frozen=True)
class TableSpec:
    number: int
    caption: str
    label: str


TABLE_SPECS = {
    1: TableSpec(1, "Performance Comparison of Smart Contract Vulnerability Detection Models", "tab:perf"),
    2: TableSpec(2, "Runtime and resource overhead during inference (median over 100 runs; warm-cache; excludes one-time model load).", "tab:runtime"),
    3: TableSpec(3, "Ablation Study: Impact of Different Modules on TEFIE-Secure Performance", "tab:ablation"),
    4: TableSpec(4, "Performance of TEFIE-Secure with Different Learning Rates", "tab:lr"),
}


def _read_pdf_text_by_page(pdf_path: str) -> List[str]:
    reader = PdfReader(pdf_path)
    pages = []
    for p in reader.pages:
        pages.append((p.extract_text() or "").replace("\u00a0", " "))
    return pages


def _find_page_containing(pages: List[str], needle: str) -> int:
    for i, t in enumerate(pages):
        if needle in t:
            return i
    raise RuntimeError(f"Could not find page containing: {needle!r}")



def _select_table_page(pages: List[str], table_no: int, must_have: List[str]) -> int:
    """Select the most likely page that contains the full table body.

    Many papers reference 'Table X' on earlier pages. This helper picks a page that
    contains the table header plus row content.
    """
    needle = f"Table {table_no}."
    candidates = [i for i, t in enumerate(pages) if needle in t]
    if not candidates:
        raise RuntimeError(f"Could not find any page containing: {needle!r}")

    def score(i: int) -> int:
        t = pages[i]
        s = 0
        for m in must_have:
            if m in t:
                s += 1
        return s

    best = max(candidates, key=lambda i: (score(i), i))
    return best

def _strip_percent(x: str) -> str:
    return x.replace("%", "")


def _to_float(x: str) -> float:
    x = x.strip()
    x = _strip_percent(x)
    return float(x)


def _parse_rows_numeric_block(lines: List[str], model_names: List[str], expected_nums_per_row: int) -> List[Tuple[str, List[str]]]:
    """Parse rows like: MODEL n1 n2 ... nK

    Model names may contain hyphens. We locate the first numeric token and treat
    everything before it as the model name.
    """
    out = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        # Normalize multi-spaces
        ln = re.sub(r"\s+", " ", ln)
        parts = ln.split(" ")
        # Find first numeric-looking token
        first_num_idx = None
        for idx, tok in enumerate(parts):
            if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?%?", tok):
                first_num_idx = idx
                break
        if first_num_idx is None:
            continue
        model = " ".join(parts[:first_num_idx])
        nums = parts[first_num_idx:]
        if model_names and model not in model_names:
            # allow minor OCR-style differences
            if model.replace(" ", "") not in {m.replace(" ", "") for m in model_names}:
                continue
        if len(nums) < expected_nums_per_row:
            raise RuntimeError(f"Row has too few numeric fields: {ln}")
        nums = nums[:expected_nums_per_row]
        out.append((model, nums))
    return out


def parse_table1(pages: List[str]) -> pd.DataFrame:
    idx = _select_table_page(pages, 1, must_have=["Performance Comparison", "DR-GCN"]) 
    text = pages[idx]
    lines = text.splitlines()

    # Extract lines between header and explanatory paragraph
    start = None
    end = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith("DR-GCN"):
            start = i
            break
    for i, ln in enumerate(lines):
        if ln.strip().startswith("What the results suggest"):
            end = i
            break
    if start is None:
        raise RuntimeError("Could not locate Table 1 rows")
    if end is None:
        end = len(lines)

    row_lines = [ln for ln in lines[start:end] if ln.strip()]
    model_names = [
        "DR-GCN",
        "TMP",
        "CGE",
        "VDM-AEI",
        "SCOBERT",
        "SCVulBERT",
        "SmartConDetect",
        "SmartGuard",
        "FELLMVP",
        "TEFIE-Secure",
    ]
    rows = _parse_rows_numeric_block(row_lines, model_names, expected_nums_per_row=12)
    if len(rows) != 10:
        raise RuntimeError(f"Expected 10 models in Table 1, got {len(rows)}")

    cols = [
        "Model",
        "Reentrancy_Acc",
        "Reentrancy_Recall",
        "Reentrancy_Prec",
        "Reentrancy_F1",
        "Timestamp_Acc",
        "Timestamp_Recall",
        "Timestamp_Prec",
        "Timestamp_F1",
        "Loops_Acc",
        "Loops_Recall",
        "Loops_Prec",
        "Loops_F1",
    ]

    data = []
    for model, nums in rows:
        data.append([model] + [float(x) for x in nums])

    return pd.DataFrame(data, columns=cols)


def parse_table2(pages: List[str]) -> pd.DataFrame:
    idx = _select_table_page(pages, 2, must_have=["Latency", "DR-GCN"]) 
    text = pages[idx]
    lines = [re.sub(r"\s+", " ", ln.strip()) for ln in text.splitlines() if ln.strip()]

    # Rows start after header line containing Params
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("Model ") and "Params" in ln:
            start = i + 1
            break
    if start is None:
        # Some PDFs place header on the next line
        for i, ln in enumerate(lines):
            if ln.startswith("DR-GCN"):
                start = i
                break
    if start is None:
        raise RuntimeError("Could not locate Table 2 rows")

    # Stop at the first bullet point line
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith("•"):
            end = i
            break

    row_lines = lines[start:end]
    model_names = [
        "DR-GCN",
        "TMP",
        "CGE",
        "VDM-AEI",
        "SCOBERT",
        "SCVulBERT",
        "SmartConDetect",
        "SmartGuard",
        "FELLMVP",
        "TEFIE-Secure",
    ]
    rows = _parse_rows_numeric_block(row_lines, model_names, expected_nums_per_row=4)
    if len(rows) != 10:
        raise RuntimeError(f"Expected 10 models in Table 2, got {len(rows)}")

    cols = ["Model", "Latency_ms", "Throughput_inst_s", "Peak_VRAM_GB", "Params_M"]
    data = []
    for model, nums in rows:
        data.append([model] + [float(x) for x in nums])
    return pd.DataFrame(data, columns=cols)


def parse_table3(pages: List[str]) -> pd.DataFrame:
    idx = _select_table_page(pages, 3, must_have=["Ablation", "w/o GCN"]) 
    text = pages[idx]
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # table rows begin with 'w/o GCN'
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("w/o GCN"):
            start = i
            break
    if start is None:
        raise RuntimeError("Could not locate Table 3 rows")

    # table ends before the next section heading
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith("5.5.2"):
            end = i
            break

    # Join wrapped method names (they appear split across lines)
    joined: List[str] = []
    i = start
    while i < end:
        ln = re.sub(r"\s+", " ", lines[i])
        if ln in {"w/o", "Feature", "Selection", "Contextual", "Embeddings", "Data", "Preprocessing"}:
            # should not happen after normalization, but keep safe
            i += 1
            continue
        if ln.startswith("w/o") and ln.endswith("%") is False and i + 1 < end and lines[i + 1].strip() == "Feature":
            # unlikely path
            pass
        # Detect the two multi-line method names in this PDF
        if ln == "w/o":
            # merge with following lines
            buf = [ln]
            j = i + 1
            while j < end and not re.search(r"%", lines[j]):
                buf.append(lines[j].strip())
                j += 1
            ln = " ".join(buf)
            i = j
            joined.append(re.sub(r"\s+", " ", ln))
            continue

        # Method names are sometimes split like:
        # w/o\nFeature\nSelection
        if ln == "w/o" and i + 3 < end:
            ln = "w/o " + lines[i + 1].strip() + " " + lines[i + 2].strip()
            i += 3
            ln = re.sub(r"\s+", " ", ln)

        if ln == "w/o Feature":
            # merge next line
            ln = "w/o Feature " + lines[i + 1].strip()
            i += 2

        # More robust: if a line has no % but the next line begins with a % block, merge
        if "%" not in ln and i + 1 < end and "%" in lines[i + 1]:
            ln = ln + " " + re.sub(r"\s+", " ", lines[i + 1])
            i += 2
            joined.append(ln)
            continue

        joined.append(ln)
        i += 1

    # Now parse 5 methods, 12 numeric % entries each
    # Normalize the 'Full Model' row label
    normalized = []
    for ln in joined:
        ln = ln.replace("(Full Model)", "(Full Model)")
        normalized.append(ln)

    # Recognize known methods
    # We'll parse by finding the first % token index and backtracking method name
    rows = []
    for ln in normalized:
        if "%" not in ln:
            continue
        ln = re.sub(r"\s+", " ", ln)
        parts = ln.split(" ")
        first_pct = None
        for idx, tok in enumerate(parts):
            if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?%", tok):
                first_pct = idx
                break
        if first_pct is None:
            continue
        method = " ".join(parts[:first_pct])
        nums = parts[first_pct:]
        if len(nums) < 12:
            raise RuntimeError(f"Table 3 row has too few numeric fields: {ln}")
        nums = nums[:12]
        rows.append((method, nums))

    if len(rows) != 5:
        raise RuntimeError(f"Expected 5 rows in Table 3, got {len(rows)}")

    cols = [
        "Method",
        "Reentrancy_Acc",
        "Reentrancy_Recall",
        "Reentrancy_Prec",
        "Reentrancy_F1",
        "Timestamp_Acc",
        "Timestamp_Recall",
        "Timestamp_Prec",
        "Timestamp_F1",
        "Loops_Acc",
        "Loops_Recall",
        "Loops_Prec",
        "Loops_F1",
    ]
    data = []
    for method, nums in rows:
        data.append([method] + [_to_float(x) for x in nums])
    return pd.DataFrame(data, columns=cols)


def parse_table4(pages: List[str]) -> pd.DataFrame:
    idx = _select_table_page(pages, 4, must_have=["Learning", "0.1"]) 
    text = pages[idx]
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # Find the first learning rate row, usually starts with 0.1
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("0.1 ") or ln.startswith("0.1"):
            start = i
            break
    if start is None:
        raise RuntimeError("Could not locate Table 4 rows")

    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith("5.6 "):
            end = i
            break

    row_lines = [re.sub(r"\s+", " ", ln) for ln in lines[start:end] if ln.strip()]

    rows = []
    for ln in row_lines:
        if not re.match(r"^[0-9]", ln):
            continue
        parts = ln.split(" ")
        lr = parts[0]
        nums = parts[1:]
        if len(nums) < 12:
            raise RuntimeError(f"Table 4 row has too few numeric fields: {ln}")
        nums = nums[:12]
        rows.append((lr, nums))

    if len(rows) != 4:
        raise RuntimeError(f"Expected 4 learning rates in Table 4, got {len(rows)}")

    cols = [
        "Learning_Rate",
        "Reentrancy_Acc",
        "Reentrancy_Recall",
        "Reentrancy_Prec",
        "Reentrancy_F1",
        "Timestamp_Acc",
        "Timestamp_Recall",
        "Timestamp_Prec",
        "Timestamp_F1",
        "Loops_Acc",
        "Loops_Recall",
        "Loops_Prec",
        "Loops_F1",
    ]
    data = []
    for lr, nums in rows:
        data.append([float(lr)] + [_to_float(x) for x in nums])
    return pd.DataFrame(data, columns=cols)


def _df_to_latex(df: pd.DataFrame, caption: str, label: str) -> str:
    """Produce a compact LaTeX table suitable for two-column papers."""

    latex_tab = df.to_latex(index=False, escape=False)
    out = []
    out.append("\\begin{table}[t]")
    out.append("\\centering")
    out.append(latex_tab.rstrip())
    out.append(f"\\caption{{{caption}}}")
    out.append(f"\\label{{{label}}}")
    out.append("\\end{table}")
    out.append("")
    return "\n".join(out)


def save_table(df: pd.DataFrame, out_dir: str, table_no: int) -> None:
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, f"table{table_no}.csv")
    tex_path = os.path.join(out_dir, f"table{table_no}.tex")
    df.to_csv(csv_path, index=False)

    spec = TABLE_SPECS[table_no]
    latex = _df_to_latex(df, spec.caption, spec.label)
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex)


def _read_roc_xlsx(path: str) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    df = pd.read_excel(path, sheet_name="Data")

    # Identify FPR column
    fpr_col = None
    for c in df.columns:
        if str(c).strip().lower() in {"fpr", "false positive rate"}:
            fpr_col = c
            break
    if fpr_col is None:
        # fallback to first column
        fpr_col = df.columns[0]

    fpr = df[fpr_col].to_numpy(dtype=float)

    tpr_cols = [c for c in df.columns if c != fpr_col]
    curves: Dict[str, np.ndarray] = {}
    for c in tpr_cols:
        name = str(c).strip()
        if name.lower().startswith("unnamed"):
            continue
        if name.lower() in {"baseline_fpr", "baseline_tpr"}:
            continue
        if name.lower() in {"random"}:
            continue
        # Clean names a bit
        name = name.replace("_TPR", "")
        name = name.replace("(AUC =", "(AUC=").replace(" )", ")")
        curves[name] = df[c].to_numpy(dtype=float)

    return fpr, curves


def plot_roc_panel(ax, xlsx_path: str, title: str) -> None:
    fpr, curves = _read_roc_xlsx(xlsx_path)

    # Sort curves to keep Proposed last
    names = list(curves.keys())
    def key(n: str) -> Tuple[int, str]:
        return (0 if "Proposed" not in n else 1, n)
    names = sorted(names, key=key)

    for name in names:
        ax.plot(fpr, curves[name], label=name)

    # Diagonal baseline
    ax.plot([0, 1], [0, 1], linestyle="--", linewidth=1, label="Random")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(title)
    ax.grid(True, linewidth=0.3)


def make_fig3_roc(assets_dir: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)

    re_path = os.path.join(assets_dir, "Reentrancy_ROC_Exact.xlsx")
    ts_path = os.path.join(assets_dir, "Timestamp_ROC_Excel_With_AxisLabels.xlsx")
    lp_path = os.path.join(assets_dir, "loops_ROC_curve_exact.xlsx")

    fig, axes = plt.subplots(1, 3, figsize=(18, 5), constrained_layout=True)
    plot_roc_panel(axes[0], re_path, "(a) Reentrancy")
    plot_roc_panel(axes[1], ts_path, "(b) Timestamp")
    plot_roc_panel(axes[2], lp_path, "(c) Loops")

    # Single legend for all
    handles, labels = axes[0].get_legend_handles_labels()
    # Merge legends from all axes
    for ax in axes[1:]:
        h, l = ax.get_legend_handles_labels()
        for hh, ll in zip(h, l):
            if ll not in labels:
                handles.append(hh)
                labels.append(ll)

    fig.legend(handles, labels, loc="lower center", ncols=5, bbox_to_anchor=(0.5, -0.02))

    png_path = os.path.join(out_dir, "fig3_roc.png")
    pdf_path = os.path.join(out_dir, "fig3_roc.pdf")
    fig.savefig(png_path, dpi=200, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)


def make_fig4_shap(assets_dir: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)

    shap_path = os.path.join(assets_dir, "SHAP_Feature_Importance_Exact.xlsx")
    df = pd.read_excel(shap_path, sheet_name="Data")

    # Keep feature order as in sheet, top-to-bottom
    features = df["Feature"].astype(str).tolist()
    y = np.arange(len(features))

    series = [
        ("Reentrancy", df["Reentrancy"].to_numpy(dtype=float)),
        ("Timestamp Dependency", df["Timestamp Dependency"].to_numpy(dtype=float)),
        ("Infinite Loop", df["Infinite Loop"].to_numpy(dtype=float)),
    ]

    fig, ax = plt.subplots(figsize=(10, 5))

    # Grouped horizontal bars
    height = 0.22
    offsets = [-height, 0.0, height]
    for (name, vals), off in zip(series, offsets):
        ax.barh(y + off, vals, height=height, label=name)

    ax.set_yticks(y)
    ax.set_yticklabels(features)
    ax.invert_yaxis()
    ax.set_xlabel("Mean |SHAP value|")
    ax.set_title("Feature importance (SHAP)")
    ax.grid(True, axis="x", linewidth=0.3)
    ax.legend(loc="lower right")

    png_path = os.path.join(out_dir, "fig4_shap.png")
    pdf_path = os.path.join(out_dir, "fig4_shap.pdf")
    fig.savefig(png_path, dpi=200, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", required=True, help="Path to the paper PDF")
    ap.add_argument("--assets", required=True, help="Directory containing the ROC/SHAP spreadsheets")
    ap.add_argument("--out", required=True, help="Output directory (tables + figs)")
    args = ap.parse_args()

    out_tables = os.path.join(args.out, "tables")
    out_figs = os.path.join(args.out, "figs")
    os.makedirs(out_tables, exist_ok=True)
    os.makedirs(out_figs, exist_ok=True)

    pages = _read_pdf_text_by_page(args.paper)

    t1 = parse_table1(pages)
    t2 = parse_table2(pages)
    t3 = parse_table3(pages)
    t4 = parse_table4(pages)

    save_table(t1, out_tables, 1)
    save_table(t2, out_tables, 2)
    save_table(t3, out_tables, 3)
    save_table(t4, out_tables, 4)

    make_fig3_roc(args.assets, out_figs)
    make_fig4_shap(args.assets, out_figs)

    print("Generated tables:")
    for i in range(1, 5):
        print(f"  - {os.path.join(out_tables, f'table{i}.csv')}")
        print(f"  - {os.path.join(out_tables, f'table{i}.tex')}")

    print("Generated figures:")
    for f in ["fig3_roc.png", "fig3_roc.pdf", "fig4_shap.png", "fig4_shap.pdf"]:
        print(f"  - {os.path.join(out_figs, f)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
