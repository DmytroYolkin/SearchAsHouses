# train_reranker

Trains a cross-encoder that re-ranks the top 20 candidates, with barcode, brand and model-number features.

Files: `component.yml` (inputs, outputs, environment, command) and `src/` (the code). Unit test: `tests/components/test_train_reranker.py`. Built in #69.

Register: `az ml component create -f azureml/components/train_reranker/component.yml` (commands run from `searchashouses/`).
