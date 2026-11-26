"""Unit tests for ingest/safetygate.py on the real samples in data/samples/ (no network)."""

import sys
from datetime import date
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]  # searchashouses/
sys.path.insert(0, str(PROJECT / "ingest"))
import safetygate  # noqa: E402

SAMPLES = PROJECT / "data" / "samples"


def sample_alerts():
    xml = (SAMPLES / "safetygate_sample.xml").read_text(encoding="utf-8")
    return safetygate.parse_report(xml, "Report-2026-46")


def test_parse_report_gives_one_flat_record_per_alert():
    alerts = sample_alerts()
    assert len(alerts) == 5
    first = alerts[0]
    assert first["alert_id"] == "SR/03255/26"
    assert first["publication_date"] == "2026-11-18"  # dd-mm-yyyy became ISO
    assert first["brand"] == "Mountain Warehouse"
    assert first["name"] == "Veste imperméable Exodus enfant"  # accents survive
    assert first["model"] == "B85-859-234-000099"
    assert first["barcode"] == "5052776274814"
    assert first["risk_types"] == ["Chemical", "Environment"]
    assert first["country_of_origin"] == "People's Republic of China"
    assert first["risk_level"] == "Serious risk"
    assert len(first["pictures"]) == 3
    assert first["report"] == "Report-2026-46"


def test_empty_fields_become_none():
    alerts = sample_alerts()
    assert alerts[0]["batch"] is None
    assert alerts[0]["recall_url"] is None
    assert alerts[2]["brand"] is None


def test_nil_fields_become_none():
    xml = (
        '<Safety-Gate xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><notifications>'
        "<caseNumber>A12/0001/24</caseNumber><publicationDate>01-02-2024</publicationDate>"
        '<barcode xsi:nil="true"/><riskType xsi:nil="true"/></notifications></Safety-Gate>'
    )
    [alert] = safetygate.parse_report(xml)
    assert alert["barcode"] is None
    assert alert["risk_types"] == []
    assert alert["pictures"] == []
    assert alert["publication_date"] == "2024-02-01"


def test_report_list_and_date_filter():
    xml = (SAMPLES / "safetygate_weekly_list_sample.xml").read_text(encoding="utf-8")
    reports = safetygate.parse_report_list(xml)
    assert [(r["reference"], r["date"]) for r in reports] == [
        ("Report-2026-46", "2026-11-20"),
        ("Report-2026-45", "2026-11-13"),
        ("Report-2026-44", "2026-11-06"),
    ]
    assert reports[0]["url"].startswith(
        "https://ec.europa.eu/safety-gate-alerts/api/download/weeklyReport/detail/xml/"
    )
    since = safetygate.reports_since(reports, date(2026, 11, 13))
    assert [r["reference"] for r in since] == ["Report-2026-46", "Report-2026-45"]
