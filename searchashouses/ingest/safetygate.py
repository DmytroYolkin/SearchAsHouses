"""Pull Safety Gate alerts from the official weekly report XML and save them (issue #13).

Run from searchashouses/:  python ingest/safetygate.py --since 2024-01-01

Source (see #4): the "Weekly Reports - XML" export of the data.europa.eu dataset
rapex-rapid-alert-system-non-food (CC0 1.0). Step 1 downloads the list of all weekly
reports, step 2 downloads every report published on or after --since. One report holds
one week of alerts, so there is no paging.

Output (git-ignored), one folder per pull date, so every raw pull is kept:
  data/raw/safetygate/<pull date>/list.xml            the report list as downloaded
  data/raw/safetygate/<pull date>/reports/<ref>.xml   every weekly report as downloaded
  data/raw/safetygate/<pull date>/alerts.jsonl        one flat JSON record per alert
"""

import argparse
import json
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path

LIST_URL = "https://ec.europa.eu/safety-gate-alerts/api/download/weeklyReport/list/xml/en"
PROJECT_DIR = Path(__file__).resolve().parents[1]  # searchashouses/
DATA_DIR = PROJECT_DIR / "data" / "raw" / "safetygate"
USER_AGENT = "safety-gate-ingest/0.1"
PAUSE_SECONDS = 0.5  # wait between downloads, to be polite to the EU server

# XML tag in a <notifications> element -> field name in our flat record
FIELDS = {
    "caseNumber": "alert_id",
    "reference": "url",
    "category": "category",
    "product": "product",
    "brand": "brand",
    "name": "name",
    "type_numberOfModel": "model",
    "batchNumber": "batch",
    "barcode": "barcode",
    "danger": "danger",
    "measures": "measures",
    "description": "description",
    "notifyingCountry": "notifying_country",
    "countryOfOrigin": "country_of_origin",
    "type": "user_type",
    "level": "risk_level",
    "onlineTrader": "online_trader",
    "URLrecall": "recall_url",
}


def text(element: ET.Element | None) -> str | None:
    """Stripped text of an element, or None when it is missing, empty or xsi:nil."""
    if element is None or element.text is None:
        return None
    return element.text.strip() or None


def parse_alert(element: ET.Element, report: str | None = None) -> dict:
    """Turn one <notifications> element (one alert) into a flat record."""
    record = {field: text(element.find(tag)) for tag, field in FIELDS.items()}
    published = text(element.find("publicationDate"))  # dd-mm-yyyy
    record["publication_date"] = (
        datetime.strptime(published, "%d-%m-%Y").date().isoformat() if published else None
    )
    risk = text(element.find("riskType"))  # e.g. "Chemical, Environment"
    record["risk_types"] = [r.strip() for r in risk.split(",") if r.strip()] if risk else []
    record["pictures"] = [p.text.strip() for p in element.iter("picture") if text(p)]
    record["report"] = report
    return record


def parse_report(xml_text: str, report: str | None = None) -> list[dict]:
    """All alerts of one weekly report."""
    root = ET.fromstring(xml_text)
    return [parse_alert(n, report) for n in root.findall("notifications")]


def parse_report_list(xml_text: str) -> list[dict]:
    """One entry per weekly report: reference, publication date (ISO) and download URL."""
    reports = []
    for item in ET.fromstring(xml_text).findall("weeklyReport"):
        published, url = text(item.find("publicationDate")), text(item.find("URL"))
        if not published or not url:
            continue
        reports.append({
            "reference": text(item.find("reference")),
            "date": datetime.strptime(published, "%d/%m/%Y").date().isoformat(),  # dd/mm/yyyy
            "url": url,
        })
    return reports


def reports_since(reports: list[dict], since: date) -> list[dict]:
    """Reports published on or after `since` (ISO dates compare correctly as strings)."""
    return [r for r in reports if r["date"] >= since.isoformat()]


def download(url: str, attempts: int = 3) -> bytes:
    """GET a URL. Retry with a growing wait on network errors, 429 and 5xx answers."""
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as error:
            client_error = isinstance(error, urllib.error.HTTPError) and error.code < 500
            if (client_error and error.code != 429) or attempt == attempts:
                raise  # a wrong URL does not get better by retrying
            wait = 2**attempt
            print(f"  retry {attempt} in {wait} s: {error}")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pull Safety Gate weekly reports, save alerts.")
    parser.add_argument("--since", required=True, type=date.fromisoformat, help="YYYY-MM-DD")
    args = parser.parse_args()

    pull_dir = DATA_DIR / date.today().isoformat()
    (pull_dir / "reports").mkdir(parents=True, exist_ok=True)

    list_xml = download(LIST_URL)
    (pull_dir / "list.xml").write_bytes(list_xml)
    reports = reports_since(parse_report_list(list_xml.decode("utf-8")), args.since)
    print(f"{len(reports)} weekly reports since {args.since}")

    alerts = []
    for i, report in enumerate(reports, 1):
        name = re.sub(r"[^A-Za-z0-9_-]", "_", report["reference"] or report["date"])
        path = pull_dir / "reports" / f"{name}.xml"
        if not path.exists():  # a re-run on the same day resumes instead of downloading again
            path.write_bytes(download(report["url"]))
            time.sleep(PAUSE_SECONDS)
        alerts.extend(parse_report(path.read_text(encoding="utf-8"), report["reference"]))
        if i % 25 == 0:
            print(f"  {i}/{len(reports)} reports, {len(alerts)} alerts so far")

    out = pull_dir / "alerts.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for alert in alerts:
            f.write(json.dumps(alert, ensure_ascii=False) + "\n")
    unique = len({a["alert_id"] for a in alerts})
    where = out.relative_to(PROJECT_DIR)
    print(f"saved {len(alerts)} alerts ({unique} unique alert IDs) to {where}")


if __name__ == "__main__":
    main()
