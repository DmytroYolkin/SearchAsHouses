# searchashouses

All project code. Commands run from this folder unless a README says otherwise.

| Folder | What it does |
|---|---|
| `azureml/setup/` | create workspace, CPU cluster and datastores; check for idle resources |
| `azureml/environments/` | training environment definitions |
| `azureml/components/` | one Azure ML component per pipeline step (`component.yml` + `src/`) |
| `azureml/pipelines/` | training pipeline and Responsible AI pipeline |
| `azureml/schedules/` | monthly retrain schedule |
| `ingest/` | pull Safety Gate alerts and ABO listings, register them as data assets |
| `services/` | gateway, models and llm-guard FastAPI services (Docker) |
| `k8s/` | Kubernetes manifests: `base/` and `overlays/` |
| `tests/` | unit, guardrail and API tests |
| `notebooks/` | data exploration |
| `data/samples/` | small samples only |
| `report/` | git-ignored: report draft, worklog, screenshots |

> Stub: every folder gets its run command here as the project grows.
