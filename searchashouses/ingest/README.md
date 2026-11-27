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

## register.py
Uploads one local pull to its datastore and registers it as the next version of a data asset (type `uri_folder`), tagged with the pull date, counts, source and licence. A pull that is already registered is skipped. Uploads use the datastore's short-lived SAS token, 4 MB blocks and 8 files at a time.

| Source (argument) | Data asset | Datastore / folder | Files uploaded |
|---|---|---|---|
| `safetygate` (default) | `safetygate_alerts` | `alerts` / `safetygate/<pull date>/` | `alerts.jsonl`, `list.xml`, `reports/*.xml` |
| `abo_listings` | `abo_listings` | `listings` / `abo/<pull date>/` | `listings.jsonl` |
| `abo_photos` | `abo_photos` | `images` / `abo/<pull date>/` | `photo_subset.csv`, `images/**/*.jpg` |

Needs `az login`, the filled `.env` and `pip install -r azureml/setup/requirements.txt`.

Run: `python ingest/register.py [safetygate|abo_listings|abo_photos] [--pull-date YYYY-MM-DD]` (default: the newest pull)
Check: `az ml data show -n <data asset> --version 1`. Test: `pytest tests/ingest/test_register.py`.

## abo.py
Downloads and parses the Amazon Berkeley Objects listings (CC BY 4.0, see the data credits in `../README.md`) and picks a reproducible photo subset. Standard library only; reuses `download()` from `safetygate.py`.

Run: `python ingest/abo.py` (options: `--photos 5000`, `--seed 42`, `--download-photos`)

1. Downloads the 16 listing files (`listings_<0-f>.json.gz`) and `images.csv.gz` from the public ABO bucket (about 95 MB) into `data/raw/abo/<pull date>/raw/`.
2. Writes `data/raw/abo/<pull date>/listings.jsonl`: one flat record per listing (item_id, language, title, titles per language, brand, model_name, model_number, category, category_path, color, description, main_image_id, country, domain_name). Language: English first, then Dutch, then French, else the first one.
3. Writes `photo_subset.csv` (item_id, image_id, path): `--photos` random main photos with a fixed `--seed`, one per product, small images only.
4. With `--download-photos`: downloads those photos (8 at a time, skipping files already there) into `data/raw/abo/<pull date>/images/`.

Test: `pytest tests/ingest/test_abo.py`.
