# TEFIE-Secure (graph)

This directory contains the reproduction entry point for the paper tables and figures.

## Run

```bash
pip install -r requirements.txt
make paper
```

## Inputs

- paper/assets/tefie_secure_paper.pdf
- paper/assets/Reentrancy_ROC_Exact.xlsx
- paper/assets/Timestamp_ROC_Excel_With_AxisLabels.xlsx
- paper/assets/loops_ROC_curve_exact.xlsx
- paper/assets/SHAP_Feature_Importance_Exact.xlsx

## Outputs

- output/tables/table1.csv, table2.csv, table3.csv, table4.csv
- output/tables/table1.tex, table2.tex, table3.tex, table4.tex
- output/figs/fig3_roc.png and fig3_roc.pdf
- output/figs/fig4_shap.png and fig4_shap.pdf
