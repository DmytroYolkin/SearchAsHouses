# train_hazard

Trains the multilingual multi-label hazard classifier: it reads a product text and gives a probability for every risk type (Chemical, Choking, Electric shock, ...), with one decision threshold per risk type. Built in #24 (code), #25 (component.yml, MLflow, cluster run); the sweep comes in #71.

## How it works
- **Input:** the `documents` output of build_pairs (`alerts.jsonl`). Only `split == "train"` alerts are used, so the test alerts stay unseen for evaluate (#27). 15% of them (random, seed 42) form a validation part.
- **Labels:** the cleaned risk types of validate_alerts. A risk type with fewer than 50 training alerts (Asphyxiation, Explosion, Security, ...) goes into Safety Gate's own catch-all label `Health risk / other`. An alert can have several labels (multi-label).
- **Model:**
  - encoder `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (50+ languages incl. Dutch and French, Apache 2.0, revision pinned)
  - mean of the token vectors
  - one linear layer with one output per label (sigmoid)
  - only the top 4 of the 12 encoder layers and the head learn, so CPU training stays short (2 layers: validation macro-F1 0.587; 4 layers: 0.654)
- **Class weights:** `pos_weight = sqrt(negatives / positives)`, capped at 30, so rare risk types are not ignored.
- **Thresholds:** for every label, the threshold (0.05 to 0.95) with the best F1 on the validation part. With fewer than 5 validation positives it stays 0.5.

## Files
| File | What |
|---|---|
| `src/hazard_labels.py` | Labels, class weights, threshold choice, F1 (standard library only, tested in CI) |
| `src/train_hazard.py` | Model, training loop, saving (needs torch + transformers: environment `train-cpu`) |

## Output folder
| Path | Content |
|---|---|
| `encoder/` | fine-tuned encoder + tokenizer (`save_pretrained`) |
| `head.pt` | weights of the linear head |
| `hazard_config.json` | base model + revision, max_length, labels, risk type -> label map, threshold per label |
| `metrics.json` | validation macro-F1 (tuned thresholds and at 0.5), F1 per label, sizes, training time |

## Run locally
From `searchashouses/`, with torch and transformers installed (same versions as `azureml/environments/train-cpu.conda.yml`):
```bash
python azureml/components/train_hazard/src/train_hazard.py --documents <build_pairs documents folder> --output <folder> --max-train 1000 --epochs 1   # quick check
python -m pytest tests/components/test_train_hazard.py
```
Register (after #25): `az ml component create -f azureml/components/train_hazard/component.yml`.
