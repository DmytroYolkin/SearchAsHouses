"""Unit test for check_idle.find_billable with a fake MLClient (no Azure calls, no cost)."""

import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

pytest.importorskip("azure.ai.ml")  # skip where the setup requirements are not installed
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azureml" / "setup"))
import check_idle  # noqa: E402


def fake_client(instance_state, cluster_nodes, endpoints, registries):
    computes = [
        NS(type="computeinstance", name="nb1", state=instance_state),
        NS(type="amlcompute", name="cpu-cluster", state=None),
    ]
    return NS(
        compute=NS(list=lambda: computes, list_nodes=lambda name: cluster_nodes),
        online_endpoints=NS(list=lambda: [NS(name=n) for n in endpoints]),
        registries=NS(list=lambda scope: [NS(name=n) for n in registries]),
    )


def test_everything_running_is_reported():
    client = fake_client("Running", ["node-1"], ["ep1"], ["reg1"])
    assert check_idle.find_billable(client) == [
        "compute instance nb1 is Running",
        "cluster cpu-cluster has 1 node(s)",
        "online endpoint ep1",
        "registry reg1",
    ]


def test_nothing_billable_when_all_is_stopped():
    client = fake_client("Stopped", [], [], [])
    assert check_idle.find_billable(client) == []
