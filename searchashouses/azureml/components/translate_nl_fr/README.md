# translate_nl_fr

Parallel job that translates English texts into Dutch and French with HuggingFace models, in mini-batches.

Files: `component.yml` (inputs, outputs, environment, command) and `src/` (the code). Unit test: `tests/components/test_translate_nl_fr.py`. Built in #36.

Register: `az ml component create -f azureml/components/translate_nl_fr/component.yml` (commands run from `searchashouses/`).
