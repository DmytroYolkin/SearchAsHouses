"""validate_alerts component: clean the raw Safety Gate alerts (issue #19; skeleton from #18).

Input:  a folder with alerts.jsonl (data asset safetygate_alerts).
Output: a folder with the cleaned alerts.jsonl and an MLTable file, so Azure ML (and later
        the Responsible AI components) can read it as a table.

Every rule comes from notebooks/01_explore_alerts.ipynb (#17) and the decisions in
.claude/context.md: all alerts are kept (also motor vehicles and "Other types of alerts").
  1. Text fields: spaces squeezed; placeholders ("Unknown", "N/A", "-", "none") become None.
  2. barcode -> barcodes: a list of valid codes (8, 12, 13 or 14 digits); glued EAN-13 codes
     are cut into 13-digit pieces; other digit runs are dropped.
  3. risk_types and category: values that differ only in case or spaces get the most common
     spelling of the whole dataset (a general rule, so new variants are caught too).
  4. risk_types: "X and Y" is split when X and Y are both known labels; "Health risk" becomes
     "Health risk / other"; repeated labels are removed. Rare labels stay: grouping them is
     the classifier's choice (#24).
  5. category: "Other - ..." categories with fewer than 10 alerts become "Other".
  6. One record per alert_id.
"""

import argparse
import json
import re
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

# MLTable file: tells Azure ML that the folder holds one JSON object per line.
MLTABLE = """paths:
  - file: ./alerts.jsonl
transformations:
  - read_json_lines:
      encoding: utf8
      include_path_column: false
"""
PLACEHOLDER = re.compile(r"^(unknown|not known|n/?a|none|-+|\?)$", re.IGNORECASE)
BARCODE_LENGTHS = {8, 12, 13, 14}  # EAN-8, UPC-A, EAN-13, GTIN-14
LABEL_ALIASES = {"health risk": "health risk / other"}  # short form found in #17
MIN_OTHER_CATEGORY = 10  # "Other - X" categories with fewer alerts become "Other"


def norm(text: str) -> str:
    """Lower case and single spaces, so two spellings of one value become equal."""
    return re.sub(r"\s+", " ", text).strip().casefold()


def tidy(value):
    """Squeeze the spaces of a text value; placeholders and empty text become None."""
    if not isinstance(value, str):
        return value
    value = re.sub(r"\s+", " ", value).strip()
    return None if not value or PLACEHOLDER.match(value) else value


def split_barcodes(value: str | None) -> list[str]:
    """Valid barcodes in a raw barcode field: digits only, glued EAN-13 codes cut apart."""
    codes = []
    for digits in re.findall(r"\d+", value or ""):
        if len(digits) in BARCODE_LENGTHS:
            codes.append(digits)
        elif len(digits) % 13 == 0:  # e.g. 26 digits = two EAN-13 codes without a separator
            codes.extend(digits[i : i + 13] for i in range(0, len(digits), 13))
    return list(dict.fromkeys(codes))  # each code once, in the original order


def spelling_map(values: Iterable[str]) -> dict[str, str]:
    """norm(value) -> the most common way it is written (ties: alphabetical, so it is stable)."""
    best: dict[str, str] = {}
    for value, _ in sorted(Counter(values).items(), key=lambda kv: (-kv[1], kv[0])):
        best.setdefault(norm(value), value)
    return best


def clean_labels(labels: list[str], spelling: dict[str, str]) -> list[str]:
    """Merge spelling variants, apply the aliases and split glued "X and Y" labels."""
    cleaned = []
    for label in labels:
        key = LABEL_ALIASES.get(norm(label), norm(label))
        parts = [part.strip() for part in key.split(" and ")]
        keys = parts if len(parts) > 1 and all(p in spelling for p in parts) else [key]
        cleaned.extend(spelling.get(k, label.strip()) for k in keys)
    return list(dict.fromkeys(cleaned))


def drop_duplicates(alerts: list[dict]) -> list[dict]:
    """Keep one record per alert_id (the first one)."""
    seen, unique = set(), []
    for alert in alerts:
        if alert["alert_id"] not in seen:
            seen.add(alert["alert_id"])
            unique.append(alert)
    return unique


def clean_alerts(alerts: list[dict]) -> tuple[list[dict], dict[str, int]]:
    """Clean all alerts; returns the cleaned alerts and counts of what changed."""
    stats = Counter(alerts_in=len(alerts))
    tidied = []
    for alert in alerts:
        record = {}
        for key, value in alert.items():
            record[key] = tidy(value)
            if isinstance(value, str) and value.strip() and record[key] is None:
                stats["placeholders_removed"] += 1
        tidied.append(record)

    label_spelling = spelling_map(t.strip() for a in tidied for t in a.get("risk_types") or [])
    category_spelling = spelling_map(a["category"] for a in tidied if a.get("category"))
    for alert in tidied:
        raw_barcode = alert.pop("barcode", None)
        alert["barcodes"] = split_barcodes(raw_barcode)
        stats["barcodes_split"] += len(alert["barcodes"]) > 1
        stats["barcode_values_dropped"] += bool(raw_barcode) and not alert["barcodes"]
        labels = alert.get("risk_types") or []
        alert["risk_types"] = clean_labels(labels, label_spelling)
        stats["risk_types_changed"] += alert["risk_types"] != labels
        if alert.get("category"):
            alert["category"] = category_spelling[norm(alert["category"])]

    category_counts = Counter(a.get("category") for a in tidied)
    for alert in tidied:
        category = alert.get("category") or ""
        if category.startswith("Other - ") and category_counts[category] < MIN_OTHER_CATEGORY:
            alert["category"] = "Other"
            stats["categories_grouped"] += 1

    cleaned = drop_duplicates(tidied)
    stats["duplicates_removed"] = len(tidied) - len(cleaned)
    stats["alerts_out"] = len(cleaned)
    return cleaned, dict(stats)


def load_alerts(folder: Path) -> list[dict]:
    """Read alerts.jsonl from the input folder."""
    with open(folder / "alerts.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_mltable(alerts: list[dict], folder: Path) -> None:
    """Write alerts.jsonl and the MLTable file into the output folder."""
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / "alerts.jsonl", "w", encoding="utf-8") as f:
        for alert in alerts:
            f.write(json.dumps(alert, ensure_ascii=False) + "\n")
    (folder / "MLTable").write_text(MLTABLE, encoding="utf-8")


def log_metrics(stats: dict[str, int]) -> None:
    """Log the counts to MLflow when it is installed (it is in the Azure ML environment)."""
    try:
        import mlflow
    except ImportError:
        return
    mlflow.log_metrics({k: float(v) for k, v in stats.items()})


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean the raw Safety Gate alerts.")
    parser.add_argument("--alerts", type=Path, required=True, help="input folder with alerts.jsonl")
    parser.add_argument("--validated", type=Path, required=True, help="output folder")
    args = parser.parse_args()

    cleaned, stats = clean_alerts(load_alerts(args.alerts))
    write_mltable(cleaned, args.validated)
    log_metrics(stats)
    print("validate_alerts:", json.dumps(stats))


if __name__ == "__main__":
    main()
