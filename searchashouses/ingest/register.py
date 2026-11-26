"""Upload a Safety Gate pull to the `alerts` datastore and register it as a data asset (issue #14).

Run from searchashouses/:  python ingest/register.py                       (newest pull)
                           python ingest/register.py --pull-date 2026-11-26
Needs `az login`, the filled .env and the packages in azureml/setup/requirements.txt.

Every new pull becomes the next version of the data asset `safetygate_alerts` (1, 2, ...).
A pull that is already registered is not registered a second time.
"""

import argparse
import json
import sys
from pathlib import Path

from azure.ai.ml import MLClient
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.entities import Data
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import ContainerClient

PROJECT_DIR = Path(__file__).resolve().parents[1]  # searchashouses/
sys.path.insert(0, str(PROJECT_DIR / "azureml" / "setup"))
from azure_config import get_ml_client  # noqa: E402  (same .env settings as the setup scripts)

ASSET_NAME = "safetygate_alerts"
DATASTORE = "alerts"
BLOCK_BYTES = 4 * 1024 * 1024
PULLS_DIR = PROJECT_DIR / "data" / "raw" / "safetygate"
SOURCE = (
    "Safety Gate weekly report XML "
    "(data.europa.eu dataset rapex-rapid-alert-system-non-food)"
)
CREDIT = (
    "Source: Safety Gate, the EU rapid alert system for dangerous non-food products "
    "(European Commission), weekly report XML, CC0 1.0."
)


def next_version(existing: list[str]) -> str:
    """The next whole-number version; "1" when the asset has no versions yet."""
    numbers = [int(v) for v in existing if v.isdigit()]
    return str(max(numbers, default=0) + 1)


def summarize(pull_dir: Path) -> dict[str, str]:
    """Tags that describe one pull. Azure ML tags are strings."""
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
        "source": SOURCE,
        "licence": "CC0-1.0",
    }


def existing_versions(ml_client: MLClient) -> list[Data]:
    try:
        return list(ml_client.data.list(name=ASSET_NAME))
    except ResourceNotFoundError:  # the asset does not exist yet
        return []


def upload(pull_dir: Path, container: ContainerClient) -> int:
    """Upload every file of the pull folder to safetygate/<pull date>/... in the container."""
    count = 0
    for path in sorted(pull_dir.rglob("*")):
        if path.is_file():
            blob_name = f"safetygate/{pull_dir.name}/{path.relative_to(pull_dir).as_posix()}"
            with open(path, "rb") as f:
                container.upload_blob(blob_name, f, overwrite=True)
            count += 1
            if count == 1 or count % 50 == 0:
                print(f"  uploaded {count} files (last: {path.name})")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Register a Safety Gate pull as a data asset.")
    parser.add_argument("--pull-date", help="folder name in data/raw/safetygate/ (default: newest)")
    args = parser.parse_args()

    if args.pull_date:
        pull_dir = PULLS_DIR / args.pull_date
    else:
        pull_dir = max(p for p in PULLS_DIR.iterdir() if p.is_dir())  # ISO names sort by date
    if not (pull_dir / "alerts.jsonl").exists():
        raise SystemExit(f"no alerts.jsonl in {pull_dir}; run ingest/safetygate.py first")
    tags = summarize(pull_dir)

    ml_client = get_ml_client()
    versions = existing_versions(ml_client)
    for asset in versions:
        if (asset.tags or {}).get("pull_date") == pull_dir.name:
            print(f"pull {pull_dir.name} is already {ASSET_NAME} version {asset.version}")
            return

    # Asking for the datastore's secrets returns a short-lived SAS token (a limited, expiring
    # permission), not the storage account key. It is used in memory only, never printed.
    store = ml_client.datastores.get(DATASTORE, include_secrets=True)
    secret = getattr(store.credentials, "sas_token", None) or store.credentials.account_key
    container = ContainerClient(
        account_url=f"https://{store.account_name}.blob.{store.endpoint}",
        container_name=store.container_name,
        credential=secret,
        # Upload bigger files in 4 MB blocks: a network hiccup then only repeats one block.
        max_single_put_size=BLOCK_BYTES,
        max_block_size=BLOCK_BYTES,
    )
    files = upload(pull_dir, container)

    version = next_version([a.version for a in versions])
    data = Data(
        name=ASSET_NAME,
        version=version,
        type=AssetTypes.URI_FOLDER,
        path=f"azureml://datastores/{DATASTORE}/paths/safetygate/{pull_dir.name}/",
        description=(
            f"Safety Gate alerts pulled on {pull_dir.name}: {tags['alerts']} alerts from "
            f"{tags['weekly_reports']} weekly reports. alerts.jsonl has one record per alert; "
            f"list.xml and reports/ hold the raw XML. {CREDIT}"
        ),
        tags=tags,
    )
    ml_client.data.create_or_update(data)
    print(f"{ASSET_NAME} version {version}: {files} files, {tags['alerts']} alerts")


if __name__ == "__main__":
    main()
