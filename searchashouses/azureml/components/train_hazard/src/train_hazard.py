"""train_hazard (#24): multilingual multi-label classifier that predicts the risk types of a text.

Input: the `documents` output of build_pairs (alerts.jsonl: alert_id, text, split, risk_types).
Only alerts with split == "train" are used; the test alerts stay unseen for evaluate (#27).

Model: a multilingual sentence encoder (mean of the token vectors) + one linear layer with one
output per risk type (sigmoid, so an alert can have several). The encoder is mostly frozen: only
its top layers learn, which keeps CPU training short. Rare risk types get a larger class weight,
and every risk type gets its own decision threshold, picked on a validation part of the training
alerts.

Output folder: encoder/ (fine-tuned encoder + tokenizer), head.pt, hazard_config.json (labels,
thresholds, base model) and metrics.json (validation F1 per label and macro-F1).
"""

import argparse
import json
import random
import time
from pathlib import Path

import hazard_labels as hl
import torch
from torch import nn
from transformers import AutoModel, AutoTokenizer

BASE_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
BASE_REVISION = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"  # pinned: the same weights every run


class HazardModel(nn.Module):
    """Encoder -> mean pooling -> dropout -> one logit per label."""

    def __init__(self, encoder, n_labels: int, dropout: float = 0.1):
        super().__init__()
        self.encoder = encoder
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(encoder.config.hidden_size, n_labels)

    def forward(self, input_ids, attention_mask):
        tokens = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
        mask = attention_mask.unsqueeze(-1).float()
        pooled = (tokens * mask).sum(1) / mask.sum(1).clamp(min=1.0)  # mean over real tokens
        return self.head(self.dropout(pooled))


def freeze_lower_layers(encoder, unfreeze_layers: int) -> int:
    """Freeze the whole encoder, then unfreeze its top `unfreeze_layers` transformer layers."""
    for parameter in encoder.parameters():
        parameter.requires_grad = False
    layers = encoder.encoder.layer
    for layer in layers[len(layers) - unfreeze_layers:] if unfreeze_layers else []:
        for parameter in layer.parameters():
            parameter.requires_grad = True
    return sum(p.numel() for p in encoder.parameters() if p.requires_grad)


def batches(n: int, size: int, rng: random.Random | None = None):
    """Index lists of `size`; shuffled when rng is given."""
    order = list(range(n))
    if rng:
        rng.shuffle(order)
    for start in range(0, n, size):
        yield order[start:start + size]


def predict(model, tokenizer, texts: list[str], max_length: int, batch_size: int = 64):
    """Probabilities (one row per text, one column per label)."""
    model.eval()
    rows = []
    with torch.no_grad():
        for idx in batches(len(texts), batch_size):
            enc = tokenizer([texts[i] for i in idx], padding=True, truncation=True,
                            max_length=max_length, return_tensors="pt")
            rows += torch.sigmoid(model(enc["input_ids"], enc["attention_mask"])).tolist()
    return rows


def train(args) -> dict:
    started = time.time()
    random.seed(args.seed)
    torch.manual_seed(args.seed)

    documents = [json.loads(line) for line in
                 (Path(args.documents) / "alerts.jsonl").open(encoding="utf-8")]
    records = [d for d in documents if d["split"] == "train"]
    if args.max_train:  # small sample for a local check
        records = random.Random(args.seed).sample(records, min(args.max_train, len(records)))
    labels, mapping = hl.label_map(records, args.min_alerts)
    train_part, val_part = hl.split_validation(records, args.val_share, args.seed)
    y_train = [hl.encode(r["risk_types"], labels, mapping) for r in train_part]
    y_val = [hl.encode(r["risk_types"], labels, mapping) for r in val_part]
    print(f"{len(train_part)} train / {len(val_part)} validation alerts, {len(labels)} labels")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, revision=args.model_revision)
    encoder = AutoModel.from_pretrained(args.model_name, revision=args.model_revision)
    trainable = freeze_lower_layers(encoder, args.unfreeze_layers)
    model = HazardModel(encoder, len(labels))
    print(f"trainable encoder parameters: {trainable:,} (top {args.unfreeze_layers} layers)")

    optimizer = torch.optim.AdamW([
        {"params": [p for p in model.encoder.parameters() if p.requires_grad], "lr": args.lr},
        {"params": model.head.parameters(), "lr": args.head_lr}])
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(hl.pos_weights(y_train)))
    texts = [r["text"] for r in train_part]
    rng = random.Random(args.seed)
    for epoch in range(1, args.epochs + 1):
        model.train()
        # The encoder stays in eval mode (no dropout): with dropout, PyTorch's fast attention
        # falls back to a slow path on CPU (measured: 1.8 s instead of 0.5 s per batch).
        # Only the head keeps its dropout.
        model.encoder.eval()
        total, steps = 0.0, 0
        for idx in batches(len(texts), args.batch_size, rng):
            enc = tokenizer([texts[i] for i in idx], padding=True, truncation=True,
                            max_length=args.max_length, return_tensors="pt")
            logits = model(enc["input_ids"], enc["attention_mask"])
            loss = loss_fn(logits, torch.tensor([y_train[i] for i in idx], dtype=torch.float))
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total, steps = total + loss.item(), steps + 1
        print(f"epoch {epoch}: train loss {total / steps:.4f} ({time.time() - started:.0f} s)")

    probs = predict(model, tokenizer, [r["text"] for r in val_part], args.max_length)
    thresholds = hl.choose_thresholds(probs, y_val)
    result = hl.scores(probs, y_val, thresholds, labels)
    at_half = hl.scores(probs, y_val, [hl.DEFAULT_THRESHOLD] * len(labels), labels)
    metrics = {"val_macro_f1": result["macro_f1"], "val_macro_f1_at_0_5": at_half["macro_f1"],
               "val_per_label_f1": result["per_label_f1"], "train_alerts": len(train_part),
               "val_alerts": len(val_part), "labels": len(labels),
               "train_seconds": round(time.time() - started)}

    out = Path(args.output)
    model.encoder.save_pretrained(out / "encoder")
    tokenizer.save_pretrained(out / "encoder")
    torch.save(model.head.state_dict(), out / "head.pt")
    config = {"base_model": args.model_name, "base_revision": args.model_revision,
              "max_length": args.max_length, "labels": labels, "label_map": mapping,
              "thresholds": dict(zip(labels, thresholds))}
    (out / "hazard_config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False),
                                            encoding="utf-8")
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--documents", required=True, help="build_pairs documents folder")
    parser.add_argument("--output", required=True, help="folder for the trained model")
    parser.add_argument("--model-name", default=BASE_MODEL)
    parser.add_argument("--model-revision", default=BASE_REVISION)
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4, help="learning rate of the encoder")
    parser.add_argument("--head-lr", type=float, default=1e-3, help="learning rate of the head")
    parser.add_argument("--max-length", type=int, default=128, help="tokens per text")
    parser.add_argument("--unfreeze-layers", type=int, default=4, help="top layers that learn")
    parser.add_argument("--val-share", type=float, default=0.15)
    parser.add_argument("--min-alerts", type=int, default=hl.MIN_ALERTS)
    parser.add_argument("--max-train", type=int, default=0, help="0 = all training alerts")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    Path(args.output).mkdir(parents=True, exist_ok=True)
    metrics = train(args)
    print(json.dumps({k: v for k, v in metrics.items() if k != "val_per_label_f1"}))


if __name__ == "__main__":
    main()
