"""Create or update the CPU training cluster `cpu-cluster` (issue #9).

Run from searchashouses/:  python azureml/setup/compute.py
min 0 nodes: the cluster costs nothing while no job runs. After a job it waits
IDLE_SECONDS and then scales back to 0. You only pay for node time while jobs run.
"""

from azure.ai.ml.entities import AmlCompute
from azure_config import get_ml_client

CLUSTER_NAME = "cpu-cluster"
# 4 vCPU, 16 GB RAM, about $0.21-0.23 per node-hour. The Azure ML quota is 6 vCPU per VM family
# (20 in total), so one 4-vCPU node fits; a second one would need 8 vCPU of the same family.
VM_SIZE = "Standard_D4s_v3"
MIN_NODES = 0
MAX_NODES = 1
IDLE_SECONDS = 120


def main() -> None:
    ml_client = get_ml_client()
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


if __name__ == "__main__":
    main()
