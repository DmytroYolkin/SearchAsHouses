"""Create the resource group and the Azure ML workspace if they do not exist yet (issue #9).

Run from searchashouses/:  python azureml/setup/workspace.py
Safe to run again: existing resources are reused, not changed.
Creating the workspace also creates a storage account, a key vault and Application Insights
(a few cents per month). A container registry is only created later, on the first image build.
"""

from azure.ai.ml.entities import Workspace
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource.resources import ResourceManagementClient  # path since version 26
from azure_config import get_ml_client, load_settings

TAGS = {"project": "searchashouses"}


def ensure_resource_group(settings: dict[str, str]) -> None:
    """Create the resource group in AZURE_LOCATION unless it already exists."""
    name = settings["AZURE_RESOURCE_GROUP"]
    groups = ResourceManagementClient(
        DefaultAzureCredential(), settings["AZURE_SUBSCRIPTION_ID"]
    ).resource_groups
    if groups.check_existence(name):
        print(f"resource group {name}: exists")
        return
    groups.create_or_update(name, {"location": settings["AZURE_LOCATION"], "tags": TAGS})
    print(f"resource group {name}: created in {settings['AZURE_LOCATION']}")


def ensure_workspace(settings: dict[str, str]) -> None:
    """Create the workspace unless it already exists."""
    name = settings["AZUREML_WORKSPACE"]
    ml_client = get_ml_client(workspace=False)
    try:
        workspace = ml_client.workspaces.get(name)
        print(f"workspace {name}: exists in {workspace.location}")
    except ResourceNotFoundError:
        workspace = Workspace(
            name=name,
            location=settings["AZURE_LOCATION"],
            display_name="SearchAsHouses",
            description="Screens BelBazaar listings against EU Safety Gate alerts.",
            tags=TAGS,
        )
        workspace = ml_client.workspaces.begin_create(workspace).result()  # takes 1-3 minutes
        print(f"workspace {name}: created in {workspace.location}")


if __name__ == "__main__":
    config = load_settings()
    ensure_resource_group(config)
    ensure_workspace(config)
