# SearchAsHouses: current state
Updated in every PR that closes an issue (see .claude/rules/context-update.md). Facts and links only.

## Status
- Current milestone: M1 Setup & data
- Done: issue plan (90 issues), labels and milestones; #6 repository skeleton (PR #91); #7 CLAUDE.md, .claude/ and templates (PR #92); #8 report skeleton (PR #93); #9 workspace and cpu-cluster (PR #94); #11 check_idle.py + auto-shutdown (PR #95); #10 datastores (PR #96); #5 budget alert (PR #97); #12 training environment (PR #98); #31 ci.yml (PR #99); #4 Safety Gate source and attribution (PR #100)
- In progress: #13 safetygate.py (PR #101)
- Next up (status:ready):
  - #1 [ci-cd] Decide how GitHub Actions logs in to Azure
  - #2 [k8s] Choose the local Kubernetes cluster and how deploy.yml reaches it
  - #3 [guardrails] Choose the LLM for the review note
  - #15 [ingest] Write ingest/abo.py and register ABO listings and a photo subset (1/2)
  - #33 [ci-cd] Fail CI when a component has no unit test
  - #40 [guardrails] Add input cleaning and PII removal (G1)

## Decisions
| Topic | Decision | Issue |
|---|---|---|
| Hand-in date | open (ask the teacher; no issue) | none |
| CPU quota and VM size | Sweden Central; `cpu-cluster` = Standard_D4s_v3 (4 vCPU, 16 GB, $0.204/h), 0-1 nodes, scale-down 120 s. Quota: 20 cores in total, 6 per family | #9 |
| Azure region | Sweden Central. Allowed by Azure for Students: germanywestcentral, swedencentral, uksouth, italynorth, norwayeast (West/North Europe and France Central are blocked) | #9 |
| Azure resources | rg-searchashouses, mlw-searchashouses (+ storage, key vault, Log Analytics, App Insights); workspace ACR created by the first environment build (#12, ~$5/month) | #9, #12 |
| Datastores | `alerts`, `images`, `index`: containers in the workspace storage account; account-key access (key read at run time, kept in the workspace key vault, never on disk) | #10 |
| Budget alert | budget `searchashouses-90`: EUR 82 (= $90 at the ECB rate of 2026-11-25; billing currency is EUR), yearly from 2026-11-01, e-mail alerts at 50/75/90% of actual cost to the Owner role. Subscription spending limit is On | #5 |
| Training environment | `train-cpu`: Azure ML builds it from base image openmpi4.1.0-ubuntu22.04:20261122.v1 + conda file (Python 3.11, torch 2.15.0+cpu, transformers 5.24.1, sentence-transformers 6.3.0, faiss-cpu 1.16.0, mlflow 3.18.0, azureml-mlflow 1.62.0.post7). Image lives in the workspace ACR (~$5/month); the GHCR alternative was declined | #12 |
| CI | `.github/workflows/ci.yml`: jobs `ruff` and `pytest` (Python 3.11, setup packages installed) on PRs to main and pushes to main; `pull_request` trigger only, read-only token. Branch protection on main requires both checks | #31 |
| GitHub-to-Azure login | open | #1 |
| Local Kubernetes and runner | open | #2 |
| LLM for the review note | open | #3 |
| Safety Gate source | Official "Weekly Reports - XML" export (data.europa.eu dataset rapex-rapid-alert-system-non-food, CC0 1.0). List of all weekly reports since 2005: `https://ec.europa.eu/safety-gate-alerts/api/download/weeklyReport/list/xml/en`; each entry has a `URL` to one report's XML (`.../weeklyReport/detail/xml/<id>?language=en...`), about 80-110 alerts per week. No paging: one file per week. Alert fields used: caseNumber, publicationDate, reference, category, product, brand, name, type_numberOfModel, batchNumber, barcode, riskType (comma-separated), danger, measures, description, notifyingCountry, countryOfOrigin, type, level, pictures. Missing fields have `xsi:nil="true"`. The internal JSON search API is undocumented: not used. Photos and brand names are third-party (not covered by the EU licence): links only, never in git | #4 |
| Safety Gate attribution (exact text, also in both READMEs) | Contains product safety alert data from Safety Gate, the EU rapid alert system for dangerous non-food products (European Commission, https://ec.europa.eu/safety-gate-alerts/), © European Union, 1995-2026. The weekly report data is published under CC0 1.0 (data.europa.eu dataset rapex-rapid-alert-system-non-food); this project parsed, cleaned and translated it. Product photos and brand names belong to their rightholders. SearchAsHouses is not affiliated with or endorsed by the European Commission. | #4 |
| Repo visibility | public since 2026-11-20: no secrets in git, issues or logs | none |
| Quiz, source zip, hand-in, stop Azure spending, module mapping, demo video | no issues; done only when I ask | none |

## Versions
| Item | Version |
|---|---|
| train-cpu environment | 1 |
| safetygate_alerts data asset | none |
| abo_listings data asset | none |
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
