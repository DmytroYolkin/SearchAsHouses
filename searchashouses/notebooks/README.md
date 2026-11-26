# notebooks

Exploration notebooks; they are the source for the components. Commands run from `searchashouses/`.

Install: `pip install -r notebooks/requirements.txt` (pandas, matplotlib, nbconvert, nbformat, ipykernel).
Run: `jupyter nbconvert --to notebook --execute notebooks/<name>.ipynb`.

| Notebook | What it shows | Issue |
|---|---|---|
| `01_explore_alerts.ipynb` | `safetygate_alerts:1`: time range, empty fields, categories, risk types, risk levels, motor vehicles, countries, barcodes, duplicates, text lengths, and the cleaning list for `validate_alerts` (#19) | #17 |

The notebooks are saved with their outputs, so they can be read on GitHub without running them.
