# SearchAsHouses

SearchAsHouses screens product listings of BelBazaar (a fictional Belgian online marketplace; listings in Dutch, French and English) against EU Safety Gate alerts on dangerous non-food products. It flags listings that look like a product from a known alert, so a human compliance officer can review them. It never decides that a product is dangerous, never removes a listing and never gives a legal conclusion.

This is an MLOps home project: training runs in Azure Machine Learning, serving runs on a local Kubernetes cluster, and GitHub Actions connects the two.

> Work in progress. Architecture, quick start, tests and data credits will be added as the project grows.

## Layout
| Path | What it holds |
|---|---|
| `searchashouses/` | all project code (see `searchashouses/README.md`) |
| `.github/` | GitHub Actions workflows and templates |
| `pyproject.toml` | ruff and pytest settings |
| `requirements-dev.txt` | lint and test tools for CI |
| `.env.example` | names of the secrets the project needs (no values) |

## Development
```bash
python -m venv .venv
.venv/Scripts/activate          # Windows; on Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check .
pytest
```

## Data credits
**Safety Gate:** Contains product safety alert data from Safety Gate, the EU rapid alert system for dangerous non-food products (European Commission, https://ec.europa.eu/safety-gate-alerts/), © European Union, 1995-2026. The weekly report data is published under CC0 1.0 (data.europa.eu dataset rapex-rapid-alert-system-non-food); this project parsed, cleaned and translated it. Product photos and brand names belong to their rightholders. SearchAsHouses is not affiliated with or endorsed by the European Commission.
