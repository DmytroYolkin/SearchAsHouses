# SearchAsHouses: context for Claude

## Project context
SearchAsHouses screens product listings of BelBazaar (a fictional Belgian online marketplace; listings in Dutch, French and English) against EU Safety Gate alerts on dangerous non-food products. It flags listings that look like a product from a known alert, for a human compliance officer. It never decides that a product is dangerous, never removes a listing and never gives a legal conclusion. This is my home project for the Howest MCT MLOps course (50% of the grade). The theory exam allows no AI, so I must be able to explain every file.

Repository: github.com/DmytroYolkin/SearchAsHouses. The repo is public: never put secrets, .env files, keys or subscription IDs in git, issues or workflow logs.

Focus: GitHub Actions connected to Azure, with reusable Azure Machine Learning pipelines built from components that Azure manages.

Three processes:
1. Training, in Azure ML only: validate_alerts -> translate_nl_fr (parallel job) -> build_pairs -> embed_images (parallel job) -> train_hazard (sweep) + train_matcher -> build_index (FAISS) -> train_reranker -> evaluate (deploy flag) -> RAI text insights -> register_bundle. Triggered by train.yml or a monthly Azure ML schedule. Only hazard, matcher and re-ranker learn weights; translation, CLIP and the LLM are used as-is. deploy.yml ships a new bundle only if the deploy flag is true.
2. Inference, on a local Kubernetes cluster (not Azure): gateway (FastAPI: /screen, /feedback, /health, /model-info), models (hazard, matcher, re-ranker; index on a PersistentVolume), llm-guard (LLM review note behind 8 guardrails), postgres (StatefulSet). During testing I play BelBazaar's backend and send requests with curl, Postman or a script.
3. Weekly index refresh: ingest.yml (GitHub Actions, Fridays) pulls new alerts and registers a new data asset version in Azure; a refresh-index CronJob adds them to the FAISS index with the existing matcher. No retraining; models change only through process 1.

Feedback loop: officer decisions -> /feedback -> postgres -> exported as a new data asset -> next training run.

Data: Safety Gate alerts (public, weekly; credit Safety Gate), Amazon Berkeley Objects listings + photo subset (CC BY 4.0), HuggingFace translation EN->NL/FR, about 50 hand-written NL/FR test listings, officer decisions.

Guardrails: G1 input cleaning + PII removal, G2 injection detector, G3 data fencing, G4 output schema, G5 citation check, G6 wording check, G7 fallback, G8 logging.

Targets: recall@10 >= 0.80 (translated) and >= 0.60 (hand-written); precision at verdict threshold >= 0.70; <= 20 false flags per 1,000 normal listings; language gap <= 10 points; hazard macro-F1 >= TF-IDF+LR baseline + 5; guardrail test set 100% caught, 0 invented references; /screen p95 < 2 s without the LLM note.

Must have: Safety Gate alerts and ABO listings as versioned data assets; pipeline validate -> build pairs -> train matcher -> build index -> evaluate -> register; hazard classifier compared with its baseline; FastAPI gateway and models service in Docker on local Kubernetes; ci.yml, train.yml and deploy.yml working end to end; review note with guardrails 1, 2, 4, 5, 7; report with screenshots, quiz answers and source zip.

Should have: translation parallel job + hand-written NL/FR test set; re-ranker + sweep on the hazard classifier; Responsible AI dashboard + scorecard; staging and production with approval; Postgres + /feedback; all 8 guardrails + guardrail test set in CI; Friday ingest + refresh-index CronJob; matcher on HuggingFace Hub with a model card.

Could have: CLIP image similarity; monthly Azure ML schedule + weekly drift check; Gradio demo Space; simple review page for officers; short demo video.

Constraints: Azure for Students, $90 credit, small CPU quota (20 cores in total, 6 per VM family), no GPU. Azure region: Sweden Central (the subscription only allows Germany West Central, Sweden Central, UK South, Italy North and Norway East). Azure ML SDK v2 and CLI v2 YAML only. Compute cluster min nodes 0; no compute instance left running; no AKS; no managed online endpoints; service images in GHCR; the training environment image is built by Azure ML in the workspace ACR (about $5/month, decided in #12). PyTorch + HuggingFace; MLflow for metrics. LLM: small local model or Azure OpenAI (not decided).

Hand-in: quiz answers (module questions, "What did you learn?", three exam questions), source code as .zip, PDF report: project/data/model, Azure ML screenshots, FastAPI integration with BelBazaar, Kubernetes extras, automation, plus Responsible AI and guardrails. Hand-in date: to confirm with the teacher. The quiz, the source zip, the hand-in itself and stopping Azure spending afterwards have no issues: they are done only when I ask.

## Repository layout
The main folder (git root) holds the files for the whole repo. The project code lives in searchashouses/, which follows the layout of the project brief. .github/ must stay at the root because GitHub only reads workflows there.
```
<repo root>/                     main folder
├── .claude/
│   ├── context.md               living project state, updated in every PR
│   └── rules/                   working rules, loaded by Claude Code at launch
│       ├── workflow.md          issue -> branch -> PR, new issues, issue format, status
│       ├── bugs.md              a bug gets its own issue, branch and PR
│       ├── context-update.md    update .claude/context.md in every PR
│       ├── report.md            worklog and report
│       ├── cost.md              Azure credit safety
│       └── conventions.md       layout, tests, versioning, explanations
├── .github/
│   ├── workflows/               ci.yml, ingest.yml, train.yml, deploy.yml, monitor.yml
│   ├── ISSUE_TEMPLATE/          bug.md, feature.md
│   └── pull_request_template.md
├── .gitignore
├── .env.example                 names of the needed secrets, no values
├── CLAUDE.md                    stable project context; imports .claude/context.md
├── README.md                    what, why, architecture, quick start, layout
├── pyproject.toml               ruff and pytest config
├── requirements-dev.txt         lint and test tools for CI
└── searchashouses/
    ├── README.md                what each folder does and the command to run it
    ├── azureml/
    │   ├── setup/               workspace, compute, datastore (SDK scripts)
    │   ├── environments/        environment definitions
    │   ├── components/          one folder per component: component.yml + src/
    │   │   ├── validate_alerts/
    │   │   ├── translate_nl_fr/
    │   │   ├── build_pairs/
    │   │   ├── embed_images/
    │   │   ├── train_hazard/
    │   │   ├── train_matcher/
    │   │   ├── build_index/
    │   │   ├── train_reranker/
    │   │   ├── evaluate/
    │   │   └── register_bundle/
    │   ├── pipelines/           train_pipeline.yml, rai_pipeline.yml
    │   └── schedules/           monthly_retrain.yml
    ├── ingest/                  safetygate.py, abo.py (run by GitHub Actions)
    ├── services/
    │   ├── gateway/             FastAPI app + Dockerfile
    │   ├── models/              hazard, matcher, re-ranker inference + Dockerfile
    │   └── llm_guard/           prompt, guardrails, fallback + Dockerfile
    ├── k8s/
    │   ├── base/                deployments, services, CronJob, Postgres StatefulSet
    │   └── overlays/            staging/, production/
    ├── tests/                   unit tests, guardrail test set, API tests
    ├── notebooks/               exploration, source for the components
    ├── data/samples/            small samples only
    └── report/                  git-ignored: report draft, worklog/, screenshots/
```

## Current state
@.claude/context.md

## Rules
Working rules live in .claude/rules/ and load automatically: workflow.md, bugs.md, context-update.md, report.md, cost.md, conventions.md.
