# ingest

Scripts that pull source data and register it as versioned Azure ML data assets: `safetygate.py` (#13, #14), `abo.py` (#15, #16) and the officer-feedback export (#67). GitHub Actions runs them every Friday (`ingest.yml`, #65).

Run: `python ingest/safetygate.py --since 2024-01-01`. Commands run from `searchashouses/`.
