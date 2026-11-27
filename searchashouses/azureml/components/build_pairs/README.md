# build_pairs

Builds (listing, alert) match pairs and hard non-matches, strips origin phrases and splits train/test by alert and time.

Files: `component.yml` (inputs, outputs, environment, command) and `src/build_pairs.py` (the code). Unit test: `tests/components/test_build_pairs.py` (#20). Skeleton in #18 (interface only: the pair steps raise NotImplementedError); logic in #20, translations in #37.

- Inputs: `alerts` (MLTable from validate_alerts), `listings` (data asset `abo_listings`, #15/#16), `test_days` (default 30).
- Outputs: `train` and `test`, each a folder with `pairs.jsonl`; no alert is in both.

Register: `az ml component create -f azureml/components/build_pairs/component.yml` (commands run from `searchashouses/`).
