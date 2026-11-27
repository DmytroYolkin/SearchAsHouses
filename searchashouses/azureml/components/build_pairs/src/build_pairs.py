"""build_pairs component: (listing, alert) pairs for the matcher (skeleton from #18, logic in #20).

Inputs:  cleaned alerts (MLTable folder from validate_alerts), ABO listings (uri_folder).
Outputs: train/pairs.jsonl and test/pairs.jsonl.

The skeleton fixes the interface (arguments, files) and reads the alerts. The steps that
need decisions or data that do not exist yet raise NotImplementedError until #20; the ABO
listing format is defined in #15.
"""

import argparse
import json
from pathlib import Path


def load_alerts(folder: Path) -> list[dict]:
    """Read alerts.jsonl from the validate_alerts output folder."""
    with open(folder / "alerts.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_listings(folder: Path) -> list[dict]:
    """Read the ABO listings. The file format is defined by ingest/abo.py in #15."""
    raise NotImplementedError("#20: needs the abo_listings format from #15")


def strip_origin(text: str) -> str:
    """Remove origin phrases ("made in ...", "ships from ...") so the matcher cannot learn
    "origin = dangerous" (notebook section 8: one country has about half of all alerts)."""
    raise NotImplementedError("#20")


def split_by_time(alerts: list[dict], test_days: int) -> tuple[list[dict], list[dict]]:
    """Alerts of the last test_days days go to test, the rest to train. Splitting by alert
    keeps every alert (and its twin products, notebook section 10) on one side only."""
    raise NotImplementedError("#20")


def make_pairs(alerts: list[dict], listings: list[dict]) -> list[dict]:
    """Match pairs (listing-like text of an alert, alert) and hard non-matches (an ABO listing
    of the same kind of product, but a different product), one dict per pair with a label."""
    raise NotImplementedError("#20")


def write_jsonl(records: list[dict], folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / "pairs.jsonl", "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build (listing, alert) pairs for the matcher.")
    parser.add_argument("--alerts", type=Path, required=True)
    parser.add_argument("--listings", type=Path, required=True)
    parser.add_argument("--test-days", type=int, default=30)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    args = parser.parse_args()

    alerts = load_alerts(args.alerts)
    listings = load_listings(args.listings)
    train_alerts, test_alerts = split_by_time(alerts, args.test_days)
    write_jsonl(make_pairs(train_alerts, listings), args.train)
    write_jsonl(make_pairs(test_alerts, listings), args.test)
    print(f"build_pairs: {len(train_alerts)} train alerts, {len(test_alerts)} test alerts")


if __name__ == "__main__":
    main()
