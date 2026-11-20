# train_matcher

Fine-tunes a small multilingual sentence encoder with a contrastive loss, to match listings to alerts.

Files: `component.yml` (inputs, outputs, environment, command) and `src/` (the code). Unit test: `tests/components/test_train_matcher.py`. Built in #21 and #22.

Register: `az ml component create -f azureml/components/train_matcher/component.yml` (commands run from `searchashouses/`).
