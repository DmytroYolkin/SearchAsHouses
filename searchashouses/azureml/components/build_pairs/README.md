# build_pairs

Builds the training and test data for the matcher (#20; skeleton from #18; translated views in #37).

- **Alert text** (what the index stores): `product. name. brand model. description`, without the country of origin.
- **Listing-like views** of an alert: a seller-style title (`brand name model`) and the description.
- **Hard negatives:** for every training alert, one ABO listing that shares the most informative (rare) words with the alert's product, name and description, never of the same brand. It is drawn from the 5 most similar listings, and one listing text is a negative for at most 20 alerts.
- **Origin phrases** ("made in <country>", "ships from ...", "gemaakt in ...", "fabriqué en ...") are removed from all texts; "manufactured in 2019" or "made in metal" stay.
- **Split:** alerts of the last `test_days` days (counted from the newest alert) go to test. The same product (same brand + model, or a shared barcode) always stays on one side.

| Output | File | Records |
|---|---|---|
| `train` | `pairs.jsonl` | anchor (view), positive (alert text), negative (ABO listing), alert_id, view, negative_source |
| `test` | `pairs.jsonl` | query, alert_id (null for normal listings), label (1 = alert view, 0 = normal listing), view |
| `documents` | `alerts.jsonl` | alert_id, text, split, category, risk_types, country_of_origin, publication_date |

Inputs: `alerts` (MLTable from validate_alerts), `listings` (`abo_listings`), `test_days` (30), `max_listings` (30,000 searched for negatives), `normal_listings` (2,000 in the test set), `seed` (42).

Files: `component.yml` and `src/build_pairs.py` (standard library only). Unit test: `tests/components/test_build_pairs.py`. Commands run from `searchashouses/`:
- Local run: `python azureml/components/build_pairs/src/build_pairs.py --alerts <validated folder> --listings data/raw/abo/<pull date> --train <out>/train --test <out>/test --documents <out>/documents`
- Register: `az ml component create -f azureml/components/build_pairs/component.yml`
