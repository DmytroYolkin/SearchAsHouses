# azureml/environments

Environment definitions for the training components (CPU only). Built in #12.

| File | What it is |
|---|---|
| `train-cpu.yml` | Azure ML environment `train-cpu`: Azure ML base image (Ubuntu 22.04) + the conda file |
| `train-cpu.conda.yml` | Python 3.11 and pinned packages: torch (CPU build), transformers, sentence-transformers, faiss-cpu, mlflow, azureml-mlflow |
| `hello_job.yml` + `hello/hello.py` | hello-world job: imports every package and logs one MLflow metric on `cpu-cluster` |

Azure ML builds the Docker image the first time a job uses the environment and keeps it in the workspace container registry (ACR, about $5/month). Change a package: bump `version` in `train-cpu.yml`.

Commands run from `searchashouses/`:
- Register: `az ml environment create -f azureml/environments/train-cpu.yml`
- Check: `az ml job create -f azureml/environments/hello_job.yml --stream` (spends a few cents of node time), then `python azureml/setup/check_idle.py`
