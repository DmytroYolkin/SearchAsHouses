# validate_alerts

Cleans the raw Safety Gate alerts: removes duplicates, standardises risk types and categories, cleans barcodes. Output: an MLTable.

Files: `component.yml` (inputs, outputs, environment, command) and `src/validate_alerts.py` (the code). Unit test: `tests/components/test_validate_alerts.py`. Skeleton in #18 (reads and writes, passes the data through); cleaning in #19.

- Input `alerts`: data asset `safetygate_alerts` (folder with `alerts.jsonl`).
- Output `validated` (MLTable): `alerts.jsonl` + an `MLTable` file (`read_json_lines`).

Local run: `python azureml/components/validate_alerts/src/validate_alerts.py --alerts data/raw/safetygate/<pull date> --validated <out folder>`

Register: `az ml component create -f azureml/components/validate_alerts/component.yml` (commands run from `searchashouses/`).
