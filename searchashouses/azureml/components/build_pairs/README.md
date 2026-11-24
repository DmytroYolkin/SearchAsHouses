# build_pairs

Builds (listing, alert) match pairs and hard non-matches, strips origin phrases and splits train/test by alert and time.

Files: `component.yml` (inputs, outputs, environment, command) and `src/` (the code). Unit test: `tests/components/test_build_pairs.py`. Built in #20 and #37.

Register: `az ml component create -f azureml/components/build_pairs/component.yml` (commands run from `searchashouses/`).
