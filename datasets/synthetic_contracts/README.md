# Synthetic example contracts

These three `.sol` files are **synthetic, hand-authored illustrative examples**
created for this artifact's offline demo. They are **not** drawn from the ESC or
VSC datasets and reproduce no third-party data. Each encodes one well-known
vulnerability pattern (reentrancy, timestamp dependence, unbounded loop) so the
demo has a labelled positive case for each task without requiring a network
download. Labels are in `labels.csv`.

For the real evaluation corpora, use `datasets/fetch_dataset.py` to download the
authentic ESC/VSC graph data from the authors' repository (see `DATASETS.md`).
