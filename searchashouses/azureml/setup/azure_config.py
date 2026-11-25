"""Shared helpers for the setup scripts: read settings from .env and build an MLClient.

The values live in the git-ignored .env file at the repo root (names in .env.example),
so the subscription ID never ends up in git. Log in first with `az login`.
"""

import os

from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from dotenv import find_dotenv, load_dotenv

REQUIRED = ["AZURE_SUBSCRIPTION_ID", "AZURE_RESOURCE_GROUP", "AZUREML_WORKSPACE", "AZURE_LOCATION"]


def load_settings() -> dict[str, str]:
    """Load .env (searched upwards from the current folder) and return the required values."""
    load_dotenv(find_dotenv(usecwd=True))
    missing = [name for name in REQUIRED if not os.getenv(name)]
    if missing:
        raise SystemExit(f"Missing in .env: {', '.join(missing)} (see .env.example)")
    return {name: os.environ[name] for name in REQUIRED}


def get_ml_client(workspace: bool = True) -> MLClient:
    """MLClient for the workspace, or for the resource group only (to create the workspace)."""
    settings = load_settings()
    return MLClient(
        credential=DefaultAzureCredential(),
        subscription_id=settings["AZURE_SUBSCRIPTION_ID"],
        resource_group_name=settings["AZURE_RESOURCE_GROUP"],
        workspace_name=settings["AZUREML_WORKSPACE"] if workspace else None,
    )
