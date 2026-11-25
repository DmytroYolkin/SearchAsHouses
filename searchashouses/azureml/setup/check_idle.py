"""List everything in Azure ML that spends credit while it runs (issue #11).

Run after any Azure work:  python searchashouses/azureml/setup/check_idle.py
Prints "nothing billable running" and exits with 0 when all is clear; otherwise it lists
what runs and exits with 1. Uses the SDK, because `az resource list` is unreliable in
Azure CLI 2.77.
"""

import sys

from azure.ai.ml import MLClient
from azure_config import get_ml_client

STOPPED_STATES = {"Stopped", "Deallocated"}


def find_billable(ml_client: MLClient) -> list[str]:
    """Return one line per resource that is spending credit right now."""
    billable = []
    for compute in ml_client.compute.list():
        if compute.type == "computeinstance" and compute.state not in STOPPED_STATES:
            billable.append(f"compute instance {compute.name} is {compute.state}")
        elif compute.type == "amlcompute":
            nodes = list(ml_client.compute.list_nodes(compute.name))
            if nodes:  # every node costs money until the cluster scales back to 0
                billable.append(f"cluster {compute.name} has {len(nodes)} node(s)")
    for endpoint in ml_client.online_endpoints.list():
        billable.append(f"online endpoint {endpoint.name}")
    for registry in ml_client.registries.list(scope="subscription"):
        billable.append(f"registry {registry.name}")
    return billable


def main() -> int:
    ml_client = get_ml_client()
    workspace = ml_client.workspaces.get(ml_client.workspace_name)
    if workspace.container_registry:  # a fixed monthly cost, not something that "runs"
        print("note: the workspace has a container registry (about $5/month)")
    billable = find_billable(ml_client)
    if billable:
        print("billable resources running:")
        for line in billable:
            print(f"- {line}")
        return 1
    print("nothing billable running")
    return 0


if __name__ == "__main__":
    sys.exit(main())
