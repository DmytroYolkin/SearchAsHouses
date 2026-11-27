"""Download and parse the Amazon Berkeley Objects (ABO) listings, pick a photo subset (issue #15).

Run from searchashouses/:  python ingest/abo.py [--photos 5000] [--seed 42] [--download-photos]

Source: the ABO dataset (CC BY 4.0, credit in ../README.md), served unpacked from its public
bucket: 16 listing files (listings/metadata/listings_<0-f>.json.gz, one JSON product per line)
and the image metadata (images/metadata/images.csv.gz). The listings are BelBazaar-like
product texts: hard non-matches for the matcher and "normal" listings for the false-flag rate.

Output (git-ignored), one folder per pull date:
  data/raw/abo/<pull date>/raw/            the downloaded files, unchanged
  data/raw/abo/<pull date>/listings.jsonl  one flat record per listing; the same product can
                                           be listed in several marketplaces (other language),
                                           so a listing is identified by item_id + domain_name
  data/raw/abo/<pull date>/photo_subset.csv  item_id, image_id, path of the chosen small photos
  data/raw/abo/<pull date>/images/<path>      the chosen photos, only with --download-photos (#16)
"""

import argparse
import csv
import gzip
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from safetygate import PAUSE_SECONDS, download  # same polite download with retries

BASE_URL = "https://amazon-berkeley-objects.s3.amazonaws.com"
LISTING_FILES = [f"listings/metadata/listings_{c}.json.gz" for c in "0123456789abcdef"]
IMAGE_FILE = "images/metadata/images.csv.gz"
PROJECT_DIR = Path(__file__).resolve().parents[1]  # searchashouses/
DATA_DIR = PROJECT_DIR / "data" / "raw" / "abo"
PREFERRED = ("en", "nl", "fr")  # BelBazaar's languages, in this order


def pick_language(entries: list[dict]) -> str | None:
    """The language tag to use for a listing: English, then Dutch, then French, else the first."""
    tags = [e.get("language_tag") for e in entries if e.get("language_tag")]
    for prefix in PREFERRED:
        for tag in tags:
            if tag.split("_")[0] == prefix:
                return tag
    return tags[0] if tags else None


def values(entries: list[dict] | None, language: str | None) -> list[str]:
    """All values of a multilingual field in one language (or untagged), else of the first."""
    entries = entries or []
    chosen = [e["value"] for e in entries if e.get("language_tag") in (language, None)]
    return [v.strip() for v in (chosen or [e["value"] for e in entries[:1]]) if v and v.strip()]


def first(entries: list[dict] | None, language: str | None) -> str | None:
    found = values(entries, language)
    return found[0] if found else None


def parse_listing(raw: dict) -> dict:
    """Turn one raw ABO product into a flat record."""
    language = pick_language(raw.get("item_name", []))
    bullets = values(raw.get("bullet_point"), language)
    return {
        "item_id": raw["item_id"],
        "language": language,
        "title": first(raw.get("item_name"), language),
        "titles": {e["language_tag"]: e["value"] for e in raw.get("item_name", [])},
        "brand": first(raw.get("brand"), language),
        "model_name": first(raw.get("model_name"), language),
        "model_number": first(raw.get("model_number"), language),
        "category": first(raw.get("product_type"), language),
        "category_path": (raw.get("node") or [{}])[0].get("node_name"),
        "color": first(raw.get("color"), language),
        "description": " ".join(bullets) or None,
        "main_image_id": raw.get("main_image_id"),
        "country": raw.get("country"),
        "domain_name": raw.get("domain_name"),
    }


def choose_photos(
    listings: list[dict], images: dict[str, dict], size: int, seed: int
) -> list[dict]:
    """A reproducible random subset of main photos, one per product: same seed and size give
    the same subset. A product sold in several marketplaces counts once (its first listing)."""
    main_images: dict[str, str] = {}
    for listing in listings:
        if listing["main_image_id"] in images:
            main_images.setdefault(listing["item_id"], listing["main_image_id"])
    candidates = sorted(main_images.items())
    chosen = random.Random(seed).sample(candidates, min(size, len(candidates)))
    return [
        {"item_id": item_id, "image_id": image_id, "path": images[image_id]["path"]}
        for item_id, image_id in sorted(chosen)
    ]


def download_photos(photos: list[dict], folder: Path, workers: int = 8) -> int:
    """Download the subset photos (small images, max 256 px) into folder/<path>.

    Downloads 8 files at a time and skips files that are already there. Products that share
    one image are downloaded once. Returns the number of files downloaded in this run.
    """
    todo = sorted({p["path"] for p in photos if not (folder / p["path"]).exists()})

    def fetch_photo(path: str) -> None:
        target = folder / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(download(f"{BASE_URL}/images/small/{path}"))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(fetch_photo, todo))  # list() waits for all and re-raises the first error
    return len(todo)


def fetch(relative: str, raw_dir: Path) -> Path:
    """Download one bucket file into raw_dir, unless it is already there (resume)."""
    path = raw_dir / relative.split("/")[-1]
    if not path.exists():
        path.write_bytes(download(f"{BASE_URL}/{relative}"))
        time.sleep(PAUSE_SECONDS)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and parse the ABO listings.")
    parser.add_argument("--photos", type=int, default=5000, help="size of the photo subset")
    parser.add_argument("--seed", type=int, default=42, help="random seed of the photo subset")
    parser.add_argument("--download-photos", action="store_true", help="also download the photos")
    args = parser.parse_args()

    pull_dir = DATA_DIR / date.today().isoformat()
    raw_dir = pull_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    listings = []
    for relative in LISTING_FILES:
        with gzip.open(fetch(relative, raw_dir), "rt", encoding="utf-8") as f:
            listings.extend(parse_listing(json.loads(line)) for line in f if line.strip())
        print(f"  {relative.split('/')[-1]}: {len(listings)} listings so far")
    with gzip.open(fetch(IMAGE_FILE, raw_dir), "rt", encoding="utf-8") as f:
        images = {row["image_id"]: row for row in csv.DictReader(f)}

    with open(pull_dir / "listings.jsonl", "w", encoding="utf-8") as f:
        for listing in listings:
            f.write(json.dumps(listing, ensure_ascii=False) + "\n")
    photos = choose_photos(listings, images, args.photos, args.seed)
    with open(pull_dir / "photo_subset.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["item_id", "image_id", "path"])
        writer.writeheader()
        writer.writerows(photos)
    print(f"saved {len(listings)} listings and {len(photos)} photos "
          f"(seed {args.seed}) to {pull_dir.relative_to(PROJECT_DIR)}")
    if args.download_photos:
        new = download_photos(photos, pull_dir / "images")
        print(f"downloaded {new} photo files to {(pull_dir / 'images').relative_to(PROJECT_DIR)}")


if __name__ == "__main__":
    main()
