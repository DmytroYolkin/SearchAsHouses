# SearchAsHouses: current state
Updated in every PR that closes an issue (see .claude/rules/context-update.md). Facts and links only.

## Status
- Current milestone: M1 Setup & data
- Done: issue plan (90 issues), labels and milestones; #6 repository skeleton (PR #91); #7 CLAUDE.md, .claude/ and templates (PR #92); #8 report skeleton (PR #93); #9 workspace and cpu-cluster (PR #94); #11 check_idle.py + auto-shutdown (PR #95); #10 datastores (PR #96); #5 budget alert (PR #97); #12 training environment (PR #98); #31 ci.yml (PR #99); #4 Safety Gate source and attribution (PR #100); #13 safetygate.py (PR #101); #14 safetygate_alerts data asset (PR #102); #17 explore alerts notebook (PR #103); #18 component skeletons (PR #104); #15 ABO ingest part 1 (PR #105); #16 ABO data assets (PR #106); #1 GitHub-to-Azure login (PR #107)
- In progress: #2 local Kubernetes cluster (PR #108)
- M1 still open: spike #3 (PR #109); all data assets are registered
- Next up (status:ready):
  - #3 [guardrails] Choose the LLM for the review note
  - #19 [azureml] Build the validate_alerts component
  - #33 [ci-cd] Fail CI when a component has no unit test (better after #20, see #104)
  - #34 [ingest] Write 25 Dutch hand-written test listings
  - #40 [guardrails] Add input cleaning and PII removal (G1)

## Decisions
| Topic | Decision | Issue |
|---|---|---|
| Hand-in date | open (ask the teacher; no issue) | none |
| CPU quota and VM size | Sweden Central; `cpu-cluster` = Standard_D4s_v3 (4 vCPU, 16 GB, $0.204/h), 0-1 nodes, scale-down 120 s. Quota: 20 cores in total, 6 per family | #9 |
| Azure region | Sweden Central. Allowed by Azure for Students: germanywestcentral, swedencentral, uksouth, italynorth, norwayeast (West/North Europe and France Central are blocked) | #9 |
| Azure resources | rg-searchashouses, mlw-searchashouses (+ storage, key vault, Log Analytics, App Insights); workspace ACR created by the first environment build (#12, ~$5/month) | #9, #12 |
| Datastores | `alerts`, `listings` (added in #16), `images`, `index`: containers in the workspace storage account; account-key access (key read at run time, kept in the workspace key vault, never on disk); uploads use the short-lived SAS token the datastore returns | #10, #16 |
| Budget alert | budget `searchashouses-90`: EUR 82 (= $90 at the ECB rate of 2026-11-25; billing currency is EUR), yearly from 2026-11-01, e-mail alerts at 50/75/90% of actual cost to the Owner role. Subscription spending limit is On | #5 |
| Training environment | `train-cpu`: Azure ML builds it from base image openmpi4.1.0-ubuntu22.04:20261122.v1 + conda file (Python 3.11, torch 2.15.0+cpu, transformers 5.24.1, sentence-transformers 6.3.0, faiss-cpu 1.16.0, mlflow 3.18.0, azureml-mlflow 1.62.0.post7). Image lives in the workspace ACR (~$5/month); the GHCR alternative was declined | #12 |
| CI | `.github/workflows/ci.yml`: jobs `ruff` and `pytest` (Python 3.11, setup packages installed) on PRs to main and pushes to main; `pull_request` trigger only, read-only token. Branch protection on main requires both checks | #31 |
| Alert filtering in validate_alerts | Keep all alerts (decided 2026-11-26): Motor vehicles (1,154 recalls, no barcodes) and "Other types of alerts" (150) stay in. Cleaning list from the notebook: "Unknown" -> empty; split glued EAN codes; risk types and categories compared case- and space-insensitively, keeping the most common spelling (general rule, not a fixed list: chemical -> Chemical, "Other - disposable electronic cigarette" -> "Other - Disposable electronic cigarette"); split glued labels ("Explosion and poisoning from inhalation" -> Explosion + Poisoning from inhalation); "Health risk" -> "Health risk / other"; group one-off "Other - ..." categories; group risk types with < 50 alerts for the classifier | #17, #19 |
| Component skeletons (#18) | Written by hand: the module 1.4 agent skill is not available in this project (decided 2026-11-26) | #18 |
| ABO source | Unpacked files from the public ABO bucket (CC BY 4.0): 16 listing files + images.csv.gz (about 95 MB, no 3 GB archive). 147,702 listings, 145,615 products: the same product can be listed in several marketplaces in another language, so a listing = item_id + domain_name. Language picked per listing: en, then nl, then fr, else the first; all titles kept. Titles in en 122,734, nl 3,555, fr 6,570; 44% phone cases (mostly amazon.in). Photo subset: 5,000 products, seed 42, small images (4,890 distinct files). Credit text in both READMEs | #15 |
| GitHub-to-Azure login | OIDC, no stored secret (same method as the course lab): app registration `github-searchashouses` with a federated credential for `repo:DmytroYolkin@104588396/SearchAsHouses@1465532844:environment:azure-ml` (the repo uses GitHub's immutable subject format with numeric IDs). Role: AzureML Data Scientist on the workspace only. GitHub environment `azure-ml` may only be used from main; environment secrets AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID (masked in logs). Workflows need `permissions: id-token: write`, `environment: azure-ml` and `azure/login@v3`. Check: `.github/workflows/azure-login-check.yml` (green) | #1 |
| Local Kubernetes and runner | k3d (k3s in Docker, as in lab 3.1): cluster `searchashouses` from `k8s/k3d-cluster.yaml`, 1 server + 1 agent, k3s v1.31.5, API https://127.0.0.1:6550, ingress http://localhost:8080 -> Traefik, StorageClass local-path; context `k3d-searchashouses`. deploy.yml reaches it through a self-hosted runner on this laptop (labels self-hosted, k8s; same user, so ~/.kube/config; started only while deploying; only push/workflow_dispatch jobs, #57), because the API listens on 127.0.0.1 only | #2 |
| LLM for the review note | open | #3 |
| Safety Gate source | Official "Weekly Reports - XML" export (data.europa.eu dataset rapex-rapid-alert-system-non-food, CC0 1.0). List of all weekly reports since 2005: `https://ec.europa.eu/safety-gate-alerts/api/download/weeklyReport/list/xml/en`; each entry has a `URL` to one report's XML (`.../weeklyReport/detail/xml/<id>?language=en...`), about 80-110 alerts per week. No paging: one file per week. Alert fields used: caseNumber, publicationDate, reference, category, product, brand, name, type_numberOfModel, batchNumber, barcode, riskType (comma-separated), danger, measures, description, notifyingCountry, countryOfOrigin, type, level, pictures. Missing fields have `xsi:nil="true"`. The internal JSON search API is undocumented: not used. Photos and brand names are third-party (not covered by the EU licence): links only, never in git | #4 |
| Safety Gate attribution (exact text, also in both READMEs) | Contains product safety alert data from Safety Gate, the EU rapid alert system for dangerous non-food products (European Commission, https://ec.europa.eu/safety-gate-alerts/), © European Union, 1995-2026. The weekly report data is published under CC0 1.0 (data.europa.eu dataset rapex-rapid-alert-system-non-food); this project parsed, cleaned and translated it. Product photos and brand names belong to their rightholders. SearchAsHouses is not affiliated with or endorsed by the European Commission. | #4 |
| Repo visibility | public since 2026-11-20: no secrets in git, issues or logs | none |
| Quiz, source zip, hand-in, stop Azure spending, module mapping, demo video | no issues; done only when I ask | none |

## Versions
| Item | Version |
|---|---|
| train-cpu environment | 1 |
| safetygate_alerts data asset | 1 (pull 2026-11-26: 12,135 alerts, 149 weekly reports, alerts 2023-12-20 to 2026-11-26; datastore `alerts`, path safetygate/2026-11-26/) |
| abo_listings data asset | 1 (pull 2026-11-27: 147,702 listings of 145,615 products; datastore `listings`, path abo/2026-11-27/) |
| abo_photos data asset | 1 (5,000 products, 4,890 small image files + photo_subset.csv; datastore `images`, path abo/2026-11-27/) |
| handwritten_test data asset | none |
| officer_feedback data asset | none |
| searchashouses-bundle | none |
| FAISS index | none |
| Service images (GHCR tag) | none |

## Latest metrics (evaluate)
recall@10 translated / hand-written, precision, false flags per 1,000, language gap, hazard macro-F1: none yet

## Azure credit
$90 left: budget shows EUR 0.00 spent (checked 2026-11-25; Azure cost data can lag up to a day)

## Open bugs and risks
- Public repo: secret scanning and push protection are off (Settings > Code security)
- Self-hosted runner on a public repo: fork PRs must never reach it (see #57)
- Git Bash rewrites arguments that start with `/` (e.g. `--scope /subscriptions/...`) into Windows paths, giving `MissingSubscription`: prefix such az commands with `MSYS_NO_PATHCONV=1`
- Local cluster needs Docker Desktop running; on this laptop host.docker.internal resolves to an unreachable IP, so k3d-cluster.yaml pins the API to 127.0.0.1
- Azure CLI 2.77: `az resource list` returns nothing and some error replies fail with "content already consumed"; use `az rest` or the SDK (check_idle.py uses the SDK). `az ml job create --stream` shows AuthenticationFailed while streaming logs although the job runs fine; read logs with `ml_client.jobs.download`

## Change log
| Date | PR | Issue | What changed |
|---|---|---|---|
| 2026-11-20 | none | none | Issue plan, labels, milestones, CLAUDE.md and .claude/ created (commit in #7) |
| 2026-11-20 | none | none | Empty "Initial commit" pushed to main, so the first issue can use a PR |
| 2026-11-20 | #91 | #6 | Repository skeleton: root files, a README in every layout folder, placeholder test (merged 2026-11-25; #7, #8, #31, #40 now ready) |
| 2026-11-25 | #92 | #7 | CLAUDE.md, .claude/context.md, .claude/rules/ and GitHub issue/PR templates on main |
| 2026-11-25 | #93 | #8 | Report skeleton (git-ignored, local only): report/report.md with all sections, worklog/, screenshots/ |
| 2026-11-25 | #94 | #9 | Setup scripts (SDK v2) for workspace and cpu-cluster; created rg-searchashouses, mlw-searchashouses and cpu-cluster in Sweden Central |
| 2026-11-25 | #95 | #11 | check_idle.py (SDK) + unit test; compute.py --instance with 30 min idle shutdown; check_idle run: nothing billable running |
| 2026-11-25 | #96 | #10 | datastores.py: containers + datastores alerts, images, index (created in Azure) |
| 2026-11-25 | #97 | #5 | Budget searchashouses-90 (EUR 82 = $90) with alerts at 50/75/90% to the Owner role |
| 2026-11-25 | #98 | #12 | Environment train-cpu:1 (Azure-built, workspace ACR) + hello-world job: Completed, all 6 packages import, MLflow metric logged |
| 2026-11-25 | #99 | #31 | ci.yml (ruff + pytest on every PR and push to main); branch protection on main requires both checks |
| 2026-11-26 | #100 | #4 | Safety Gate source (official weekly report XML, CC0), fields, attribution text in both READMEs; XML samples in data/samples/ |
| 2026-11-26 | #101 | #13 | ingest/safetygate.py + 4 unit tests; pull --since 2024-01-01: 149 weekly reports, 12,135 alerts (local data/raw/safetygate/2026-11-26/) |
| 2026-11-26 | #102 | #14 | ingest/register.py + 3 unit tests; safetygate_alerts version 1 registered (151 files in datastore alerts, 12,135 alerts) |
| 2026-11-26 | #103 | #17 | notebooks/01_explore_alerts.ipynb (executed, with outputs) + notebooks/requirements.txt; cleaning list and open filtering decision for #19 |
| 2026-11-26 | #104 | #18 | Hand-written skeletons: validate_alerts (runs, passes data through, writes MLTable) and build_pairs (interface, steps raise NotImplementedError); component spec test for every component.yml |
| 2026-11-27 | #105 | #15 | ingest/abo.py + 6 unit tests + data/samples/abo_sample.json; ABO credit in both READMEs; run: 147,702 listings, 5,000-photo subset (local data/raw/abo/2026-11-27/) |
| 2026-11-27 | #106 | #16 | listings datastore; abo.py --download-photos; register.py generalized (safetygate, abo_listings, abo_photos); abo_listings v1 and abo_photos v1 registered |
| 2026-11-28 | #107 | #1 | OIDC login from GitHub Actions: app github-searchashouses (federated credential, no secret), AzureML Data Scientist on the workspace, environment azure-ml (main only); azure-login-check.yml green |
| 2026-11-28 | #108 | #2 | k3d cluster searchashouses from k8s/k3d-cluster.yaml (2 nodes Ready, ingress on localhost:8080); runner plan for deploy.yml |
