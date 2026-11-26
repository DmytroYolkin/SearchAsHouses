# ingest

Scripts that pull source data and register it as versioned Azure ML data assets: `safetygate.py` (#13, #14), `abo.py` (#15, #16) and the officer-feedback export (#67). GitHub Actions runs them every Friday (`ingest.yml`, #65). Commands run from `searchashouses/`.

## safetygate.py
Pulls Safety Gate alerts from the official weekly report XML (CC0, see the data credits in `../README.md`). Standard library only.

Run: `python ingest/safetygate.py --since 2024-01-01`

1. Downloads the list of all weekly reports, then every report published on or after `--since` (one XML file per week, about 80-110 alerts).
2. Saves everything under `data/raw/safetygate/<pull date>/` (git-ignored):
   - `list.xml`: the report list as downloaded
   - `reports/<ref>.xml`: every weekly report as downloaded
   - `alerts.jsonl`: one flat record per alert (alert_id, publication_date, category, product, brand, name, model, batch, barcode, risk_types, danger, measures, description, notifying_country, country_of_origin, user_type, risk_level, pictures, report, ...)

A second run on the same day reuses the reports already downloaded. Test: `pytest tests/ingest/test_safetygate.py`.
