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

## Data credits
**Safety Gate:** Contains product safety alert data from Safety Gate, the EU rapid alert system for dangerous non-food products (European Commission, https://ec.europa.eu/safety-gate-alerts/), © European Union, 1995-2026. The weekly report data is published under CC0 1.0 (data.europa.eu dataset rapex-rapid-alert-system-non-food); this project parsed, cleaned and translated it. Product photos and brand names belong to their rightholders. SearchAsHouses is not affiliated with or endorsed by the European Commission.

**Amazon Berkeley Objects (ABO):** Product listings and images from the Amazon Berkeley Objects dataset (https://amazon-berkeley-objects.s3.amazonaws.com/index.html), licensed under CC BY 4.0. Credit for the data, including all images: Amazon.com. Credit for building the dataset: Matthieu Guillaumin, Thomas Dideriksen, Kenan Deng, Himanshu Arora, Arnab Dhua, Xi (Brian) Zhang, Tomas Yago-Vicente (Amazon.com), Jasmine Collins, Shubham Goel, Jitendra Malik (UC Berkeley); J. Collins et al., "ABO: Dataset and Benchmarks for Real-World 3D Object Understanding", CVPR 2022. This project parsed, filtered and translated the listings.

Samples in `data/samples/`:
- `safetygate_sample.xml`: the first 5 of 104 alerts of Safety Gate weekly report 2026-46, otherwise unchanged
- `safetygate_weekly_list_sample.xml`: the first 3 entries of the weekly report list
- `abo_sample.json`: 5 unchanged ABO listings (Dutch, English + Hindi, German, one without bullet points, US English)
