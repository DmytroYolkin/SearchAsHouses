"""Hello-world job for the train-cpu environment (issue #12).

Imports every training package, prints its version and logs one MLflow metric.
A green run proves that the environment builds and that MLflow tracking works on cpu-cluster.
"""

import importlib

import mlflow
import torch

PACKAGES = ["torch", "transformers", "sentence_transformers", "faiss", "mlflow", "azureml.mlflow"]


def main() -> None:
    for name in PACKAGES:
        module = importlib.import_module(name)
        print(f"{name}: {getattr(module, '__version__', 'imported')}")
    print(f"CUDA available: {torch.cuda.is_available()} (expected False: CPU-only build)")
    mlflow.log_metric("packages_imported", len(PACKAGES))
    print("train-cpu environment OK")


if __name__ == "__main__":
    main()
