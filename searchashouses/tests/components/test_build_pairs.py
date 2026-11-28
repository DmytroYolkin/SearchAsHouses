"""Unit tests for the build_pairs component (#20). Standard library only, no Azure."""

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]  # searchashouses/
sys.path.insert(0, str(PROJECT / "azureml" / "components" / "build_pairs" / "src"))
import build_pairs as bp  # noqa: E402

ORIGIN = bp.origin_pattern({"People's Republic of China", "Italy"})


def alert(alert_id, day, **fields):
    base = {"alert_id": alert_id, "publication_date": f"2026-{day}", "product": "Musical toy",
            "name": "Xylophone", "brand": None, "model": None, "barcodes": [],
            "description": "Wooden xylophone with eight metal strips", "category": "Toys",
            "risk_types": ["Choking"], "country_of_origin": "People's Republic of China"}
    return {**base, **fields}


def listing(item_id, title, brand="Other brand"):
    return {"item_id": item_id, "domain_name": "amazon.com", "title": title, "brand": brand,
            "description": None}


def test_origin_phrases_are_removed_in_three_languages():
    assert bp.strip_origin("Wooden xylophone. Made in China.", ORIGIN) == "Wooden xylophone."
    assert bp.strip_origin("Ships from People's Republic of China, fast", ORIGIN) == "fast"
    assert bp.strip_origin("Houten xylofoon, gemaakt in China", ORIGIN) == "Houten xylofoon"
    assert bp.strip_origin("Xylophone en bois fabriqué en Chine", ORIGIN) == "Xylophone en bois"
    assert bp.strip_origin("Lamp, made in Italy", ORIGIN) == "Lamp"


def test_other_uses_of_made_in_are_kept():
    for text in ["Manufactured in 2019 and 2020.", "The fasteners are made in metal.",
                 "Plug made in protection class II."]:
        assert bp.strip_origin(text, ORIGIN) == text


def test_alert_text_and_views():
    a = alert("A1", "11-01", brand="Flying Tiger", model="3033045",
              description="Xylophone with a wooden frame. Made in China.")
    assert bp.alert_text(a, ORIGIN) == (
        "Musical toy. Xylophone. Flying Tiger 3033045. Xylophone with a wooden frame.")
    assert "China" not in bp.alert_text(a, ORIGIN)  # neither the phrase nor the origin field
    assert bp.listing_views(a, ORIGIN) == [
        ("title", "Flying Tiger Xylophone 3033045"),
        ("description", "Xylophone with a wooden frame.")]
    assert bp.listing_views(alert("A2", "11-01", name=None, description="Toy"), ORIGIN) == [
        ("title", "Musical toy")]  # a one-word description is not a useful view


def test_no_alert_is_in_both_train_and_test():
    alerts = [
        alert("OLD", "01-10"),
        alert("NEW", "11-20"),
        alert("TWIN-OLD", "02-01", brand="BamBam", model="6669"),  # same product as TWIN-NEW
        alert("TWIN-NEW", "11-15", brand="bambam", model="6669"),
        alert("CODE-OLD", "03-01", barcodes=["5905523648812"]),  # same barcode as CODE-NEW
        alert("CODE-NEW", "11-10", barcodes=["5905523648812"]),
    ]
    train, test, moved = bp.split_by_time(alerts, test_days=30)
    train_ids, test_ids = {a["alert_id"] for a in train}, {a["alert_id"] for a in test}
    assert not train_ids & test_ids
    assert train_ids | test_ids == {a["alert_id"] for a in alerts}
    assert train_ids == {"OLD"}
    assert moved == 2  # TWIN-OLD and CODE-OLD follow their recent twin into test


def test_similar_listings_share_rare_words_and_skip_the_same_brand():
    listings = [listing("L1", "Wooden xylophone for toddlers", brand="Flying Tiger"),
                listing("L2", "Wooden xylophone with mallets"),
                listing("L3", "Phone case black")]
    index = bp.ListingIndex(listings, ORIGIN)
    assert index.similar("xylophone", exclude_brand=None)[:2] == [0, 1]
    assert index.similar("xylophone", exclude_brand="flying tiger") == [1]
    assert index.similar("lawnmower", exclude_brand=None) == []


def test_build_end_to_end():
    alerts = [alert(f"T{i}", f"0{1 + i % 8}-01", brand=f"Brand{i}") for i in range(8)]
    alerts += [alert("RECENT", "11-20", brand="Peppa Pig")]
    listings = [listing(f"L{i}", f"Wooden xylophone number {i}") for i in range(20)]
    train, test, documents, stats = bp.build(alerts, listings, test_days=30, max_listings=15,
                                             normal_listings=5, seed=1)
    train_alerts = {t["alert_id"] for t in train}
    test_alerts = {t["alert_id"] for t in test if t["alert_id"]}
    assert test_alerts == {"RECENT"} and not train_alerts & test_alerts
    normal_texts = {t["query"] for t in test if t["label"] == 0}
    assert len(normal_texts) == 5 and not normal_texts & {t["negative"] for t in train}
    assert {t["view"] for t in train} == {"title", "description"}
    assert all(t["negative_source"] == "similar" for t in train)
    assert {d["alert_id"]: d["split"] for d in documents}["RECENT"] == "test"
    assert len(documents) == len(alerts)
    assert stats["alerts_train"] == 8 and stats["test_normal_listings"] == 5
