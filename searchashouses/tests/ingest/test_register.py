"""Unit tests for ingest/register.py: versions, tags, file selection (no Azure calls)."""

import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("azure.ai.ml")  # skip where the setup requirements are not installed
PROJECT = Path(__file__).resolve().parents[2]  # searchashouses/
sys.path.insert(0, str(PROJECT / "ingest"))
import register  # noqa: E402


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def test_first_version_is_1():
    assert register.next_version([]) == "1"


def test_next_version_follows_the_highest_number():
    assert register.next_version(["1", "3", "2"]) == "4"
    assert register.next_version(["1", "draft"]) == "2"  # non-numeric versions are ignored


def test_summarize_alerts_counts_alerts_reports_and_dates(tmp_path):
    pull = tmp_path / "2026-11-26"
    (pull / "reports").mkdir(parents=True)
    (pull / "reports" / "Report-2026-46.xml").write_text("<Safety-Gate/>")
    (pull / "reports" / "Report-2026-45.xml").write_text("<Safety-Gate/>")
    write_jsonl(pull / "alerts.jsonl", [
        {"alert_id": "A1", "publication_date": "2026-11-13"},
        {"alert_id": "A2", "publication_date": "2026-11-18"},
        {"alert_id": "A2", "publication_date": None},
    ])
    tags = register.summarize_alerts(pull)
    assert tags["pull_date"] == "2026-11-26"
    assert tags["alerts"] == "3"
    assert tags["unique_alert_ids"] == "2"
    assert tags["weekly_reports"] == "2"
    assert tags["first_alert_date"] == "2026-11-13"
    assert tags["last_alert_date"] == "2026-11-18"
    assert tags["licence"] == "CC0-1.0"
    assert all(isinstance(v, str) for v in tags.values())  # Azure ML tags must be strings


def test_summarize_listings_counts_products_and_languages(tmp_path):
    pull = tmp_path / "2026-11-27"
    pull.mkdir()
    write_jsonl(pull / "listings.jsonl", [
        {"item_id": "B1", "titles": {"en_CA": "Brogue"}},
        {"item_id": "B1", "titles": {"nl_NL": "Brogue voor dames"}},  # same product, other shop
        {"item_id": "B2", "titles": {"fr_FR": "Chaise", "en_GB": "Chair"}},
    ])
    tags = register.summarize_listings(pull)
    assert (tags["listings"], tags["products"]) == ("3", "2")
    assert (tags["titles_en"], tags["titles_nl"], tags["titles_fr"]) == ("2", "1", "1")
    assert tags["licence"] == "CC-BY-4.0"


def test_summarize_photos_needs_every_photo_on_disk(tmp_path):
    pull = tmp_path / "2026-11-27"
    (pull / "images" / "aa").mkdir(parents=True)
    (pull / "photo_subset.csv").write_text(
        "item_id,image_id,path\nB1,i1,aa/1.jpg\nB2,i1,aa/1.jpg\nB3,i2,aa/2.jpg\n")
    (pull / "images" / "aa" / "1.jpg").write_bytes(b"jpg")
    with pytest.raises(SystemExit):  # aa/2.jpg is not downloaded yet
        register.summarize_photos(pull)
    (pull / "images" / "aa" / "2.jpg").write_bytes(b"jpg")
    tags = register.summarize_photos(pull)
    assert (tags["products"], tags["image_files"]) == ("3", "2")


def test_files_to_upload_only_takes_the_matching_files(tmp_path):
    pull = tmp_path / "2026-11-27"
    for name in ["listings.jsonl", "photo_subset.csv", "raw/listings_0.json.gz", "images/aa/1.jpg"]:
        (pull / name).parent.mkdir(parents=True, exist_ok=True)
        (pull / name).write_text("x")
    listings = register.SOURCES["abo_listings"].patterns
    photos = register.SOURCES["abo_photos"].patterns
    names = lambda files: [f.relative_to(pull).as_posix() for f in files]  # noqa: E731
    assert names(register.files_to_upload(pull, listings)) == ["listings.jsonl"]
    assert names(register.files_to_upload(pull, photos)) == ["images/aa/1.jpg", "photo_subset.csv"]


def test_every_description_can_be_filled_from_its_tags():
    examples = {
        "safetygate": {"pull_date": "d", "alerts": "1", "weekly_reports": "1"},
        "abo_listings": {"pull_date": "d", "listings": "1", "products": "1"},
        "abo_photos": {"pull_date": "d", "products": "1", "image_files": "1"},
    }
    for name, source in register.SOURCES.items():
        assert "CC" in source.about.format(**examples[name])  # the licence is in the credit
