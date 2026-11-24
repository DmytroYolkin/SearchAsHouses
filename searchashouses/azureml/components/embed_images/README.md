# embed_images

Parallel job that embeds product photos with CLIP for image similarity.

Files: `component.yml` (inputs, outputs, environment, command) and `src/` (the code). Unit test: `tests/components/test_embed_images.py`. Built in #76.

Register: `az ml component create -f azureml/components/embed_images/component.yml` (commands run from `searchashouses/`).
