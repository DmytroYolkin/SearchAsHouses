"""Create or update the CPU training cluster `cpu-cluster` (issues #9 and #11).

Run from searchashouses/:  python azureml/setup/compute.py
min 0 nodes: the cluster costs nothing while no job runs. After a job it waits
IDLE_SECONDS and then scales back to 0. You only pay for node time while jobs run.

The project does not need a compute instance (a notebook VM). If one is ever needed, create
it only with `python azureml/setup/compute.py --instance <name>`, so it shuts itself down
after INSTANCE_IDLE_MINUTES without activity. Delete it when done.
"""

import argparse

from azure.ai.ml import MLClient
from azure.ai.ml.entities import AmlCompute, ComputeInstance
from azure_config import get_ml_client

CLUSTER_NAME = "cpu-cluster"
# 4 vCPU, 16 GB RAM, about $0.20 per node-hour in Sweden Central. The Azure ML quota is 6 vCPU
# per VM family (20 in total), so one 4-vCPU node fits; a second one would need 8 vCPU.
VM_SIZE = "Standard_D4s_v3"
MIN_NODES = 0
MAX_NODES = 1
IDLE_SECONDS = 120

INSTANCE_SIZE = "Standard_D2s_v3"  # 2 vCPU: fits next to the cluster node in the 6-vCPU quota
INSTANCE_IDLE_MINUTES = 30


def create_cluster(ml_client: MLClient) -> None:
    cluster = AmlCompute(
        name=CLUSTER_NAME,
        size=VM_SIZE,
        min_instances=MIN_NODES,
        max_instances=MAX_NODES,
        idle_time_before_scale_down=IDLE_SECONDS,
        tier="dedicated",
    )
    cluster = ml_client.compute.begin_create_or_update(cluster).result()
    print(
        f"{cluster.name}: {cluster.size}, nodes {cluster.min_instances}-{cluster.max_instances}, "
        f"scale down after {cluster.idle_time_before_scale_down} s"
    )


def create_instance(ml_client: MLClient, name: str) -> None:
    """Create a compute instance that shuts down after INSTANCE_IDLE_MINUTES idle minutes."""
    instance = ComputeInstance(
        name=name,
        size=INSTANCE_SIZE,
        idle_time_before_shutdown_minutes=INSTANCE_IDLE_MINUTES,
    )
    ml_client.compute.begin_create_or_update(instance).result()
    print(f"{name}: {INSTANCE_SIZE}, shuts down after {INSTANCE_IDLE_MINUTES} idle minutes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--instance", metavar="NAME", help="create a compute instance instead")
    args = parser.parse_args()
    if args.instance:
        create_instance(get_ml_client(), args.instance)
    else:
        create_cluster(get_ml_client())
