"""Every azureml/components/*/component.yml loads with the Azure ML SDK (no Azure calls)."""

from pathlib import Path

import pytest

pytest.importorskip("azure.ai.ml")  # skip where the setup requirements are not installed
from azure.ai.ml import load_component  # noqa: E402

COMPONENTS = Path(__file__).resolve().parents[2] / "azureml" / "components"
SPECS = sorted(COMPONENTS.glob("*/component.yml"))


@pytest.mark.parametrize("spec", SPECS, ids=[p.parent.name for p in SPECS])
def test_component_spec_loads_and_matches_its_folder(spec):
    component = load_component(source=spec)  # fails on YAML or schema errors
    assert component.name == spec.parent.name
    assert (spec.parent / "src").is_dir()
    # The SDK stores "azureml:train-cpu:1" without its "azureml:" prefix.
    assert str(component.environment).removeprefix("azureml:") == "train-cpu:1"
