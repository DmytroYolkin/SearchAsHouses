# build_index

Embeds all alerts with the matcher and builds the FAISS index.

Files: `component.yml` (inputs, outputs, environment, command) and `src/` (the code). Unit test: `tests/components/test_build_index.py`. Built in #23.

Register: `az ml component create -f azureml/components/build_index/component.yml` (commands run from `searchashouses/`).
