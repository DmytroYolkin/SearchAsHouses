# register_bundle

Registers matcher, index and hazard classifier as one model (`searchashouses-bundle`), tagged with the data asset versions and the git commit.

Files: `component.yml` (inputs, outputs, environment, command) and `src/` (the code). Unit test: `tests/components/test_register_bundle.py`. Built in #29.

Register: `az ml component create -f azureml/components/register_bundle/component.yml` (commands run from `searchashouses/`).
