# validate_alerts

Cleans the raw Safety Gate alerts into one tidy table (#19; skeleton from #18). All alerts are kept (decision on #17/#18).

Rules (from `notebooks/01_explore_alerts.ipynb`):
1. Text fields: spaces squeezed; placeholders (`Unknown`, `N/A`, `-`, `none`) become empty.
2. `barcode` becomes `barcodes`: a list of valid codes (8, 12, 13 or 14 digits); glued EAN-13 codes are cut apart; other digit runs are dropped.
3. `risk_types` and `category`: spelling variants (case, spaces) get the most common spelling of the whole dataset (a general rule).
4. `risk_types`: glued "X and Y" labels are split; `Health risk` becomes `Health risk / other`. Rare labels stay; the classifier groups them (#24).
5. `category`: "Other - ..." categories with fewer than 10 alerts become `Other`.
6. One record per `alert_id`.

- Input `alerts`: data asset `safetygate_alerts` (folder with `alerts.jsonl`).
- Output `validated` (MLTable): `alerts.jsonl` + an `MLTable` file (`read_json_lines`).
- The counts of every change are printed and logged to MLflow.

Files: `component.yml` and `src/validate_alerts.py`. Unit test: `tests/components/test_validate_alerts.py`. Commands run from `searchashouses/`:
- Local run: `python azureml/components/validate_alerts/src/validate_alerts.py --alerts data/raw/safetygate/<pull date> --validated <out folder>`
- Register: `az ml component create -f azureml/components/validate_alerts/component.yml`
