"""validate_alerts component: clean the raw Safety Gate alerts (skeleton from #18, logic in #19).

Input:  a folder with alerts.jsonl (data asset safetygate_alerts).
Output: a folder with the cleaned alerts.jsonl and an MLTable file, so Azure ML (and later
        the Responsible AI components) can read it as a table.

The skeleton already reads and writes the data, so the component can run end to end; the
cleaning steps below only pass the data through until #19 fills them in. Every rule comes
from notebooks/01_explore_alerts.ipynb (#17).
"""

import argparse
import json
from pathlib import Path

# MLTable file: tells Azure ML that the folder holds one JSON object per line.
MLTABLE = """paths:
  - file: ./alerts.jsonl
transformations:
  - read_json_lines:
      encoding: utf8
      include_path_column: false
"""


def load_alerts(folder: Path) -> list[dict]:
    """Read alerts.jsonl from the input folder."""
    with open(folder / "alerts.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def clean_alert(alert: dict) -> dict:
    """Clean one alert. Skeleton: returns an unchanged copy.

    #19 adds (notebook sections 5, 8, 9 and 12):
    - placeholder "Unknown" (origin, barcode, ...) becomes None
    - barcode: digits only; glued EAN codes are split into a list of codes
    - category and risk types: compared case- and space-insensitively, keeping the most
      common spelling; glued labels ("X and Y") are split; "Health risk" becomes
      "Health risk / other"; one-off "Other - ..." categories are grouped
    """
    return dict(alert)


def drop_duplicates(alerts: list[dict]) -> list[dict]:
    """Keep one record per alert_id (first one wins). Skeleton: already works, #19 tests it."""
    seen, unique = set(), []
    for alert in alerts:
        if alert["alert_id"] not in seen:
            seen.add(alert["alert_id"])
            unique.append(alert)
    return unique


def write_mltable(alerts: list[dict], folder: Path) -> None:
    """Write alerts.jsonl and the MLTable file into the output folder."""
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / "alerts.jsonl", "w", encoding="utf-8") as f:
        for alert in alerts:
            f.write(json.dumps(alert, ensure_ascii=False) + "\n")
    (folder / "MLTable").write_text(MLTABLE, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean the raw Safety Gate alerts.")
    parser.add_argument("--alerts", type=Path, required=True, help="input folder with alerts.jsonl")
    parser.add_argument("--validated", type=Path, required=True, help="output folder")
    args = parser.parse_args()

    raw = load_alerts(args.alerts)
    cleaned = drop_duplicates([clean_alert(a) for a in raw])
    write_mltable(cleaned, args.validated)
    print(f"validate_alerts: {len(raw)} alerts in, {len(cleaned)} alerts out")


if __name__ == "__main__":
    main()
