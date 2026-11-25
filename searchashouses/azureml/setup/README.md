# azureml/setup

Python scripts (SDK v2) that create the Azure resources the project needs. Each script is safe to run again.

| Script | What it does | Issue |
|---|---|---|
| `azure_config.py` | reads `.env` and builds an `MLClient` (shared by the other scripts) | #9 |
| `workspace.py` | resource group `rg-searchashouses` + workspace `mlw-searchashouses` | #9 |
| `compute.py` | CPU cluster `cpu-cluster`: Standard_D4s_v3, 0-1 nodes, scale-down after 120 s. `--instance NAME` creates a compute instance that shuts down after 30 idle minutes (only if ever needed) | #9, #11 |
| `datastores.py` | containers + datastores `alerts`, `images`, `index` in the workspace storage account (account-key access; the key goes straight to the workspace key vault) | #10 |
| `check_idle.py` | lists running compute instances, cluster nodes, online endpoints and registries; exit 0 + "nothing billable running" when clear | #11 |

Before the first run (commands run from `searchashouses/`):
1. `az login`
2. Fill in `.env` at the repo root (names in `.env.example`; `AZURE_LOCATION=swedencentral`).
3. `pip install -r azureml/setup/requirements.txt`

Run: `python azureml/setup/workspace.py`, then `python azureml/setup/compute.py`, then `python azureml/setup/datastores.py`.
Check: `az ml compute show -n cpu-cluster --query min_instances` prints `0` (after `az configure --defaults group=rg-searchashouses workspace=mlw-searchashouses`).
After any Azure work: `python azureml/setup/check_idle.py` must print `nothing billable running`.

Region: Azure for Students only allows Germany West Central, Sweden Central, UK South, Italy North and Norway East for this subscription; Sweden Central is the cheapest of these for Standard_D4s_v3.
