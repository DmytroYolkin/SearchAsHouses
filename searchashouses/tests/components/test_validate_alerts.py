"""Unit tests for the validate_alerts component (skeleton from #18; #19 adds the cleaning tests)."""

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]  # searchashouses/
sys.path.insert(0, str(PROJECT / "azureml" / "components" / "validate_alerts" / "src"))
import validate_alerts  # noqa: E402

ALERTS = [
    {"alert_id": "SR/0001/26", "brand": "A", "barcode": "5052776274814"},
    {"alert_id": "SR/0002/26", "brand": None, "barcode": None},
    {"alert_id": "SR/0001/26", "brand": "A", "barcode": "5052776274814"},  # duplicate
]


def test_drop_duplicates_keeps_the_first_record_per_alert_id():
    unique = validate_alerts.drop_duplicates(ALERTS)
    assert [a["alert_id"] for a in unique] == ["SR/0001/26", "SR/0002/26"]


def test_reads_and_writes_alerts_and_an_mltable_file(tmp_path):
    source, target = tmp_path / "in", tmp_path / "out"
    source.mkdir()
    (source / "alerts.jsonl").write_text("\n".join(json.dumps(a) for a in ALERTS) + "\n")

    alerts = validate_alerts.load_alerts(source)
    validate_alerts.write_mltable(validate_alerts.drop_duplicates(alerts), target)

    lines = (target / "alerts.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    mltable = (target / "MLTable").read_text(encoding="utf-8")
    assert "file: ./alerts.jsonl" in mltable and "read_json_lines" in mltable
