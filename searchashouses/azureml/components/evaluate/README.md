# evaluate

Scores the models and the baselines on the test split, logs every target metric to MLflow and sets the deploy flag.

Files: `component.yml` (inputs, outputs, environment, command) and `src/` (the code). Unit test: `tests/components/test_evaluate.py`. Built in #26, #27 and #28.

Register: `az ml component create -f azureml/components/evaluate/component.yml` (commands run from `searchashouses/`).
