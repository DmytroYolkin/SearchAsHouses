# SearchAsHouses: current state
Updated in every PR that closes an issue (see .claude/rules/context-update.md). Facts and links only.

## Status
- Current milestone: M1 Setup & data
- Done: issue plan (90 issues), labels and milestones; #6 repository skeleton (PR #91)
- In progress: #7 CLAUDE.md, .claude/ and GitHub templates (PR #92, waiting for review)
- Next up (status:ready):
  - #1 [ci-cd] Decide how GitHub Actions logs in to Azure
  - #2 [k8s] Choose the local Kubernetes cluster and how deploy.yml reaches it
  - #3 [guardrails] Choose the LLM for the review note
  - #4 [ingest] Confirm the Safety Gate API fields and attribution wording
  - #5 [setup] Set a budget alert on the Azure subscription
  - #8 [report] Set up the report skeleton and worklog folders (PR after #92 is merged: it only changes this file)
  - #9 [setup] Script the workspace and a CPU cluster that scales to 0 (SDK v2)
  - #31 [ci-cd] Add ci.yml: lint and unit tests on every PR
  - #40 [guardrails] Add input cleaning and PII removal (G1)

## Decisions
| Topic | Decision | Issue |
|---|---|---|
| Hand-in date | open (ask the teacher; no issue) | none |
| CPU quota and VM size | open | #9 |
| GitHub-to-Azure login | open | #1 |
| Local Kubernetes and runner | open | #2 |
| LLM for the review note | open | #3 |
| Safety Gate API and attribution | open | #4 |
| Repo visibility | public since 2026-11-20: no secrets in git, issues or logs | none |
| Quiz, source zip, hand-in, stop Azure spending, module mapping, demo video | no issues; done only when I ask | none |

## Versions
| Item | Version |
|---|---|
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
$90 left (checked 2026-11-20)

## Open bugs and risks
- Public repo: secret scanning and push protection are off (Settings > Code security)
- Self-hosted runner on a public repo: fork PRs must never reach it (see #57)

## Change log
| Date | PR | Issue | What changed |
|---|---|---|---|
| 2026-11-20 | none | none | Issue plan, labels, milestones, CLAUDE.md and .claude/ created (commit in #7) |
| 2026-11-20 | none | none | Empty "Initial commit" pushed to main, so the first issue can use a PR |
| 2026-11-20 | #91 | #6 | Repository skeleton: root files, a README in every layout folder, placeholder test (merged 2026-11-25; #7, #8, #31, #40 now ready) |
| 2026-11-25 | #92 | #7 | CLAUDE.md, .claude/context.md, .claude/rules/ and GitHub issue/PR templates on main |
