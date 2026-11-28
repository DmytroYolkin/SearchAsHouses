"""Unit tests for the validate_alerts component (#19), with the cases found in notebook #17."""

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]  # searchashouses/
sys.path.insert(0, str(PROJECT / "azureml" / "components" / "validate_alerts" / "src"))
import validate_alerts as va  # noqa: E402


def alert(alert_id, **fields):
    base = {"alert_id": alert_id, "category": "Toys", "barcode": None, "risk_types": ["Choking"]}
    return {**base, **fields}


def test_placeholders_and_extra_spaces_are_cleaned():
    assert va.tidy("Unknown") is None
    assert va.tidy(" n/a ") is None
    assert va.tidy("-") is None
    assert va.tidy("none") is None
    assert va.tidy("Other -  Bath  screen") == "Other - Bath screen"
    assert va.tidy("Flying Tiger") == "Flying Tiger"
    assert va.tidy(["a list stays"]) == ["a list stays"]


def test_barcodes_keep_valid_codes_and_split_glued_ean13():
    assert va.split_barcodes("5052776274814") == ["5052776274814"]
    glued = "69708903881726970890388196"  # two EAN-13 codes without a separator
    assert va.split_barcodes(glued) == ["6970890388172", "6970890388196"]
    assert va.split_barcodes("6970890388165  " + glued) == [
        "6970890388165", "6970890388172", "6970890388196"]
    assert va.split_barcodes("12345678 / 012345678905") == ["12345678", "012345678905"]
    assert va.split_barcodes("1234567890") == []  # 10 digits: not a valid length
    assert va.split_barcodes("Unknown") == []
    assert va.split_barcodes(None) == []


def test_spelling_map_picks_the_most_common_spelling():
    spelling = va.spelling_map(["Chemical"] * 5 + ["chemical"] * 2 + ["Fire"])
    assert spelling == {"chemical": "Chemical", "fire": "Fire"}


def test_labels_are_merged_aliased_split_and_deduplicated():
    spelling = va.spelling_map(["Chemical", "Chemical", "chemical", "Explosion",
                                "Poisoning from inhalation", "Health risk / other",
                                "Explosion and Poisoning from Inhalation"])
    assert va.clean_labels(["chemical"], spelling) == ["Chemical"]
    assert va.clean_labels(["Health risk"], spelling) == ["Health risk / other"]
    assert va.clean_labels(["Burns", "Explosion and poisoning from inhalation "], spelling) == [
        "Burns", "Explosion", "Poisoning from inhalation"]
    assert va.clean_labels(["Explosion", "explosion"], spelling) == ["Explosion"]


def test_clean_alerts_end_to_end():
    alerts = [
        alert("A1", barcode="69708903881726970890388196", risk_types=["chemical"],
              country_of_origin="Unknown", category="Other - disposable electronic cigarette"),
        alert("A2", risk_types=["Chemical"], category="Other - Disposable electronic cigarette"),
        alert("A3", risk_types=["Chemical"], category="Other - Telescopic Ladder"),
        alert("A1", risk_types=["Fire"]),  # repeated alert_id
    ]
    cleaned, stats = va.clean_alerts(alerts)
    first = cleaned[0]
    assert [a["alert_id"] for a in cleaned] == ["A1", "A2", "A3"]
    assert first["barcodes"] == ["6970890388172", "6970890388196"] and "barcode" not in first
    assert first["risk_types"] == ["Chemical"]
    assert first["country_of_origin"] is None
    # both spellings become one category; with fewer than 10 alerts it is grouped into "Other"
    assert {a["category"] for a in cleaned} == {"Other"}
    assert stats["alerts_in"] == 4 and stats["alerts_out"] == 3
    assert stats["duplicates_removed"] == 1
    assert stats["barcodes_split"] == 1
    assert stats["placeholders_removed"] == 1


def test_big_other_categories_keep_their_name():
    alerts = [alert(f"A{i}", category="Other - Disposable electronic cigarette") for i in range(10)]
    cleaned, _ = va.clean_alerts(alerts)
    assert {a["category"] for a in cleaned} == {"Other - Disposable electronic cigarette"}


def test_reads_and_writes_alerts_and_an_mltable_file(tmp_path):
    source, target = tmp_path / "in", tmp_path / "out"
    source.mkdir()
    rows = [alert("A1"), alert("A2"), alert("A1")]
    (source / "alerts.jsonl").write_text("\n".join(json.dumps(a) for a in rows) + "\n")

    cleaned, _ = va.clean_alerts(va.load_alerts(source))
    va.write_mltable(cleaned, target)

    lines = (target / "alerts.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    mltable = (target / "MLTable").read_text(encoding="utf-8")
    assert "file: ./alerts.jsonl" in mltable and "read_json_lines" in mltable
