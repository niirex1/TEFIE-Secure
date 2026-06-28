"""One-command reproduction entry point.

Usage:
    python reproduce.py            # tables + figures + workbook from data/
    python reproduce.py --synth    # (re)generate synthetic smoke-test data first

Outputs land in outputs/. With the shipped SYNTHETIC data this produces
well-formed but non-paper results; point data/ at your real experimental outputs
(see data/SCHEMA.md) to reproduce the manuscript.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--synth", action="store_true",
                    help="regenerate synthetic smoke-test data before running")
    args = ap.parse_args()

    if args.synth:
        import make_synthetic_data
        make_synthetic_data.build_all()
        print("[1/4] synthetic smoke-test data written to data/ (NOT paper values)")
    else:
        print("[1/4] using existing data/ (run with --synth to regenerate smoke-test data)")

    import tables
    tables.build_all()
    print("[2/4] tables   -> outputs/table_*.csv")

    import figures
    figures.build_all()
    print("[3/4] figures  -> outputs/*-ROC.pdf, outputs/feature-importance.pdf")

    import workbook
    path = workbook.build()
    print(f"[4/4] workbook -> {path}")
    print("done.")


if __name__ == "__main__":
    main()
