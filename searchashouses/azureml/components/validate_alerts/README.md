# validate_alerts

Cleans the raw Safety Gate alerts: removes duplicates, standardises risk types and categories, cleans barcodes. Output: an MLTable.

Files: `component.yml` (inputs, outputs, environment, command) and `src/` (the code). Unit test: `tests/components/test_validate_alerts.py`. Built in #19.

Register: `az ml component create -f azureml/components/validate_alerts/component.yml` (commands run from `searchashouses/`).
