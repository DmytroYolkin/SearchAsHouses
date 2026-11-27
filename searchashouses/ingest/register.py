"""Upload a local pull to an Azure ML datastore and register it as a data asset (#14, #16).

Run from searchashouses/:
  python ingest/register.py                  Safety Gate alerts  -> safetygate_alerts
  python ingest/register.py abo_listings     ABO listings        -> abo_listings
  python ingest/register.py abo_photos       ABO photo subset    -> abo_photos
  add --pull-date 2026-11-27 to pick a pull folder instead of the newest one
Needs `az login`, the filled .env and the packages in azureml/setup/requirements.txt.

Every new pull becomes the next version of its data asset (1, 2, ...). A pull that is
already registered is not registered a second time.
"""

import argparse
import csv
import json
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from azure.ai.ml import MLClient
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.entities import Data
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import ContainerClient

PROJECT_DIR = Path(__file__).resolve().parents[1]  # searchashouses/
sys.path.insert(0, str(PROJECT_DIR / "azureml" / "setup"))
from azure_config import get_ml_client  # noqa: E402  (same .env settings as the setup scripts)

RAW_DIR = PROJECT_DIR / "data" / "raw"
BLOCK_BYTES = 4 * 1024 * 1024
SAFETYGATE_SOURCE = (
    "Safety Gate weekly report XML (data.europa.eu dataset rapex-rapid-alert-system-non-food)"
)
SAFETYGATE_CREDIT = (
    "Source: Safety Gate, the EU rapid alert system for dangerous non-food products "
    "(European Commission), weekly report XML, CC0 1.0."
)
ABO_CREDIT = (
    "Source: Amazon Berkeley Objects (ABO) dataset, CC BY 4.0. Credit for the data: "
    "Amazon.com; dataset by J. Collins et al., CVPR 2022."
)


def summarize_alerts(pull_dir: Path) -> dict[str, str]:
    """Tags for a Safety Gate pull. Azure ML tags are strings."""
    with open(pull_dir / "alerts.jsonl", encoding="utf-8") as f:
        alerts = [json.loads(line) for line in f]
    dates = sorted(a["publication_date"] for a in alerts if a["publication_date"])
    return {
        "pull_date": pull_dir.name,
        "alerts": str(len(alerts)),
        "unique_alert_ids": str(len({a["alert_id"] for a in alerts})),
        "weekly_reports": str(len(list((pull_dir / "reports").glob("*.xml")))),
        "first_alert_date": dates[0] if dates else "",
        "last_alert_date": dates[-1] if dates else "",
        "source": SAFETYGATE_SOURCE,
        "licence": "CC0-1.0",
    }


def summarize_listings(pull_dir: Path) -> dict[str, str]:
    """Tags for the ABO listings: counts and how many listings have an en/nl/fr title."""
    with open(pull_dir / "listings.jsonl", encoding="utf-8") as f:
        listings = [json.loads(line) for line in f]

    def with_title(prefix: str) -> str:
        return str(sum(any(t.startswith(prefix + "_") for t in x["titles"]) for x in listings))

    return {
        "pull_date": pull_dir.name,
        "listings": str(len(listings)),
        "products": str(len({x["item_id"] for x in listings})),
        "titles_en": with_title("en"),
        "titles_nl": with_title("nl"),
        "titles_fr": with_title("fr"),
        "source": "Amazon Berkeley Objects listings (amazon-berkeley-objects.s3.amazonaws.com)",
        "licence": "CC-BY-4.0",
    }


def summarize_photos(pull_dir: Path) -> dict[str, str]:
    """Tags for the ABO photo subset. Stops when photos of the list are not downloaded."""
    with open(pull_dir / "photo_subset.csv", encoding="utf-8") as f:
        photos = list(csv.DictReader(f))
    paths = {p["path"] for p in photos}
    missing = [p for p in paths if not (pull_dir / "images" / p).exists()]
    if missing:
        hint = "run: python ingest/abo.py --download-photos"
        raise SystemExit(f"{len(missing)} photos are not downloaded yet; {hint}")
    return {
        "pull_date": pull_dir.name,
        "products": str(len(photos)),
        "image_files": str(len(paths)),
        "source": "Amazon Berkeley Objects small images (max 256 px)",
        "licence": "CC-BY-4.0",
    }


@dataclass(frozen=True)
class Source:
    asset: str  # data asset name
    datastore: str  # target datastore (#10, #16)
    folder: str  # local folder in data/raw/ and blob folder in the datastore
    patterns: tuple[str, ...]  # which files of a pull to upload; the first one must exist
    summarize: Callable[[Path], dict[str, str]]
    about: str  # description; {tag} placeholders are filled from the tags


SOURCES = {
    "safetygate": Source(
        "safetygate_alerts", "alerts", "safetygate", ("alerts.jsonl", "list.xml", "reports/*.xml"),
        summarize_alerts,
        "Safety Gate alerts pulled on {pull_date}: {alerts} alerts from {weekly_reports} weekly "
        "reports. alerts.jsonl has one record per alert; list.xml and reports/ hold the raw XML. "
        + SAFETYGATE_CREDIT,
    ),
    "abo_listings": Source(
        "abo_listings", "listings", "abo", ("listings.jsonl",),
        summarize_listings,
        "ABO product listings pulled on {pull_date}: {listings} listings of {products} products "
        "(listings.jsonl, one flat record per listing; a listing is item_id + domain_name). "
        + ABO_CREDIT,
    ),
    "abo_photos": Source(
        "abo_photos", "images", "abo", ("photo_subset.csv", "images/**/*.jpg"),
        summarize_photos,
        "ABO photo subset of {pull_date}: one small main photo for each of {products} products "
        "({image_files} image files in images/, listed in photo_subset.csv). " + ABO_CREDIT,
    ),
}


def next_version(existing: list[str]) -> str:
    """The next whole-number version; "1" when the asset has no versions yet."""
    numbers = [int(v) for v in existing if v.isdigit()]
    return str(max(numbers, default=0) + 1)


def files_to_upload(pull_dir: Path, patterns: tuple[str, ...]) -> list[Path]:
    """The files of a pull that match the patterns, each once, in a fixed order."""
    return sorted({p for pattern in patterns for p in pull_dir.glob(pattern) if p.is_file()})


def existing_versions(ml_client: MLClient, asset: str) -> list[Data]:
    try:
        return list(ml_client.data.list(name=asset))
    except ResourceNotFoundError:  # the asset does not exist yet
        return []


def upload(files: list[Path], pull_dir: Path, folder: str, container: ContainerClient) -> None:
    """Upload the files to <folder>/<pull date>/... in the container, 8 at a time."""

    def upload_one(path: Path) -> None:
        blob_name = f"{folder}/{pull_dir.name}/{path.relative_to(pull_dir).as_posix()}"
        with open(path, "rb") as f:
            container.upload_blob(blob_name, f, overwrite=True)

    with ThreadPoolExecutor(max_workers=8) as pool:
        for done, _ in enumerate(pool.map(upload_one, files), 1):
            if done == 1 or done % 500 == 0 or done == len(files):
                print(f"  uploaded {done}/{len(files)} files")


def main() -> None:
    parser = argparse.ArgumentParser(description="Register a local pull as an Azure ML data asset.")
    parser.add_argument("source", nargs="?", default="safetygate", choices=sorted(SOURCES))
    parser.add_argument("--pull-date", help="pull folder name (default: the newest pull)")
    args = parser.parse_args()
    source = SOURCES[args.source]

    pulls = RAW_DIR / source.folder
    if args.pull_date:
        pull_dir = pulls / args.pull_date
    else:  # ISO folder names sort by date, so max() is the newest pull with the main file
        ready = [p for p in pulls.iterdir() if (p / source.patterns[0]).exists()]
        pull_dir = max(ready, default=None)
    if pull_dir is None or not (pull_dir / source.patterns[0]).exists():
        raise SystemExit(f"no {source.patterns[0]} in {pulls}; run the ingest script first")
    tags = source.summarize(pull_dir)

    ml_client = get_ml_client()
    versions = existing_versions(ml_client, source.asset)
    for asset in versions:
        if (asset.tags or {}).get("pull_date") == pull_dir.name:
            print(f"pull {pull_dir.name} is already {source.asset} version {asset.version}")
            return

    # Asking for the datastore's secrets returns a short-lived SAS token (a limited, expiring
    # permission), not the storage account key. It is used in memory only, never printed.
    store = ml_client.datastores.get(source.datastore, include_secrets=True)
    secret = getattr(store.credentials, "sas_token", None) or store.credentials.account_key
    container = ContainerClient(
        account_url=f"https://{store.account_name}.blob.{store.endpoint}",
        container_name=store.container_name,
        credential=secret,
        # Upload bigger files in 4 MB blocks: a network hiccup then only repeats one block.
        max_single_put_size=BLOCK_BYTES,
        max_block_size=BLOCK_BYTES,
    )
    files = files_to_upload(pull_dir, source.patterns)
    upload(files, pull_dir, source.folder, container)

    version = next_version([a.version for a in versions])
    data = Data(
        name=source.asset,
        version=version,
        type=AssetTypes.URI_FOLDER,
        path=f"azureml://datastores/{source.datastore}/paths/{source.folder}/{pull_dir.name}/",
        description=source.about.format(**tags),
        tags=tags,
    )
    ml_client.data.create_or_update(data)
    print(f"{source.asset} version {version}: {len(files)} files")


if __name__ == "__main__":
    main()
