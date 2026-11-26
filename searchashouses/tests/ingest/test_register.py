"""Unit tests for ingest/register.py: version numbering and pull tags (no Azure calls)."""

import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("azure.ai.ml")  # skip where the setup requirements are not installed
PROJECT = Path(__file__).resolve().parents[2]  # searchashouses/
sys.path.insert(0, str(PROJECT / "ingest"))
import register  # noqa: E402


def test_first_version_is_1():
    assert register.next_version([]) == "1"


def test_next_version_follows_the_highest_number():
    assert register.next_version(["1", "3", "2"]) == "4"
    assert register.next_version(["1", "draft"]) == "2"  # non-numeric versions are ignored


def test_summarize_counts_alerts_reports_and_dates(tmp_path):
    pull = tmp_path / "2026-11-26"
    (pull / "reports").mkdir(parents=True)
    (pull / "reports" / "Report-2026-46.xml").write_text("<Safety-Gate/>")
    (pull / "reports" / "Report-2026-45.xml").write_text("<Safety-Gate/>")
    alerts = [
        {"alert_id": "A1", "publication_date": "2026-11-13"},
        {"alert_id": "A2", "publication_date": "2026-11-18"},
        {"alert_id": "A2", "publication_date": None},
    ]
    (pull / "alerts.jsonl").write_text("\n".join(json.dumps(a) for a in alerts) + "\n")

    tags = register.summarize(pull)
    assert tags["pull_date"] == "2026-11-26"
    assert tags["alerts"] == "3"
    assert tags["unique_alert_ids"] == "2"
    assert tags["weekly_reports"] == "2"
    assert tags["first_alert_date"] == "2026-11-13"
    assert tags["last_alert_date"] == "2026-11-18"
    assert tags["licence"] == "CC0-1.0"
    assert all(isinstance(v, str) for v in tags.values())  # Azure ML tags must be strings
