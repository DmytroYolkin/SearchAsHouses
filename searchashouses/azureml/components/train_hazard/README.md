# train_hazard

Trains the multilingual multi-label hazard classifier, with one threshold per risk type.

Files: `component.yml` (inputs, outputs, environment, command) and `src/` (the code). Unit test: `tests/components/test_train_hazard.py`. Built in #24, #25 (sweep in #71).

Register: `az ml component create -f azureml/components/train_hazard/component.yml` (commands run from `searchashouses/`).
