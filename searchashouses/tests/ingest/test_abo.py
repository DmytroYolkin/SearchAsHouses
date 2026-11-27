"""Unit tests for ingest/abo.py on real ABO records in data/samples/abo_sample.json (no network)."""

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]  # searchashouses/
sys.path.insert(0, str(PROJECT / "ingest"))
import abo  # noqa: E402

RAW = json.loads((PROJECT / "data" / "samples" / "abo_sample.json").read_text(encoding="utf-8"))
LISTINGS = {r["item_id"]: abo.parse_listing(r) for r in RAW}


def test_dutch_listing_becomes_a_flat_record():
    shoe = LISTINGS["B06X9STHNG"]
    assert shoe["language"] == "nl_NL"
    assert shoe["title"].startswith("Amazon-merk - vinden. Dames Leder")
    assert shoe["brand"] == "find."
    assert shoe["model_name"] == "37753"
    assert shoe["model_number"] == "12-05-04"
    assert shoe["category"] == "SHOES"
    assert shoe["category_path"] == "/Categorieën/Dames/Schoenen/Pumps"
    assert shoe["description"] == "Schoen in Loafer-stijl Platform hak Cap teen Middenhak"
    assert shoe["main_image_id"] == "81iZlv3bjpL"
    assert shoe["domain_name"] == "amazon.nl"


def test_english_is_preferred_and_all_titles_are_kept():
    loafers = LISTINGS["B0846BTJ34"]
    assert loafers["language"] == "en_IN"  # English wins over Hindi
    assert loafers["title"].startswith("Stanton Men's Brown Loafers")
    assert set(loafers["titles"]) == {"en_IN", "hi_IN"}


def test_first_language_when_no_preferred_one_exists():
    assert LISTINGS["B08F9YCCDF"]["language"] == "de_DE"
    assert LISTINGS["B08F9YCCDF"]["title"].startswith("UMI Seide Kissenbezug")


def test_missing_fields_become_none():
    sofa = LISTINGS["B07CTPR73M"]
    assert sofa["description"] is None
    assert sofa["model_name"] is None
    assert sofa["model_number"] == "25020039-01"


def test_photo_subset_is_reproducible_and_only_uses_known_images():
    listings = list(LISTINGS.values())
    images = {listing["main_image_id"]: {"path": f"xx/{listing['main_image_id']}.jpg"}
              for listing in listings[:4]}  # the 5th listing has no image metadata
    first_run = abo.choose_photos(listings, images, size=3, seed=42)
    assert first_run == abo.choose_photos(listings, images, size=3, seed=42)
    assert len(first_run) == 3
    assert all(p["image_id"] in images for p in first_run)
    assert len(abo.choose_photos(listings, images, size=99, seed=42)) == 4  # capped


def test_a_product_in_two_marketplaces_gets_one_photo():
    shoe = LISTINGS["B06X9STHNG"]
    same_shoe_elsewhere = {**shoe, "domain_name": "amazon.ca", "main_image_id": "OTHER"}
    images = {"81iZlv3bjpL": {"path": "aa/1.jpg"}, "OTHER": {"path": "bb/2.jpg"}}
    photos = abo.choose_photos([shoe, same_shoe_elsewhere], images, size=10, seed=1)
    assert photos == [{"item_id": "B06X9STHNG", "image_id": "81iZlv3bjpL", "path": "aa/1.jpg"}]
