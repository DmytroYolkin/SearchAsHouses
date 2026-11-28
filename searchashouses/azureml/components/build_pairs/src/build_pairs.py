"""build_pairs component: (listing, alert) pairs for the matcher (issue #20; skeleton from #18).

Inputs:  cleaned alerts (MLTable folder from validate_alerts), ABO listings (abo_listings).
Outputs: train/pairs.jsonl      triplets (anchor = listing-like text, positive = alert text,
                                negative = a similar ABO listing of another brand)
         test/pairs.jsonl       queries: views of test alerts (label 1) + normal ABO listings
                                (label 0, alert_id null) for the false-flag rate
         documents/alerts.jsonl the alert text for every alert (used by build_index, evaluate)

There are no real listings of recalled products, so the "listing-like" texts are views of the
alert itself: a seller-style title (brand name model) and the description. Translated views
come in #37. Standard library only, so the unit tests also run in CI.
"""

import argparse
import json
import math
import random
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ORIGIN_TRIGGERS = [  # English, Dutch, French
    "made in", "manufactured in", "produced in", "assembled in", "imported from",
    "ships from", "shipped from", "shipping from", "dispatched from",
    "country of origin:", "country of origin", "origin:",
    "gemaakt in", "geproduceerd in", "vervaardigd in", "verzonden vanuit", "verzonden uit",
    "herkomst:", "fabriqué en", "fabriqué au", "fabriqué aux", "fabriqué à",
    "expédié de", "expédié depuis", "origine :", "origine:",
]
COUNTRY_ALIASES = [  # short and translated names next to the names used in the alerts
    "China", "PRC", "P.R.C.", "P.R. China", "Chine", "Hong Kong", "Taiwan", "India", "Inde",
    "Turkey", "Turkije", "Turquie", "Vietnam", "Viet Nam", "Bangladesh", "Pakistan",
    "Italy", "Italië", "Italie", "Germany", "Duitsland", "Allemagne", "France", "Frankrijk",
    "Spain", "Spanje", "Espagne", "Poland", "Polen", "Pologne", "EU", "Europe", "USA", "UK",
]
STOPWORDS = set(
    "the and for with from this that are has have was not all new set pack pcs piece pieces "
    "size one two black white blue red green pink grey gray men women kids child children "
    "voor met van een het de en op aan uit pour avec les des une est dans sur par".split()
)
MAX_DF_SHARE = 0.01  # words in more than 1% of the listings are too common to show similarity
MIN_DF_CAP = 50  # ... but a word in up to 50 listings always counts (matters for small pools)
TOP_CANDIDATES = 5  # the negative is drawn from the 5 most similar listings ...
MAX_NEGATIVE_USES = 20  # ... and one listing is a negative for at most 20 alerts


def norm(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip().casefold()


def origin_pattern(countries: set[str]) -> re.Pattern:
    """A regex for "made in <country>", "ships from <country>", ... in EN, NL and FR."""
    names = sorted({c for c in countries | set(COUNTRY_ALIASES) if c}, key=len, reverse=True)
    triggers = sorted(ORIGIN_TRIGGERS, key=len, reverse=True)
    trigger = "|".join(re.escape(t) for t in triggers)
    country = "|".join(re.escape(n) for n in names)
    return re.compile(rf"\b(?:{trigger})\s*(?:the\s+)?(?:{country})(?![\w])\.?", re.IGNORECASE)


def strip_origin(text: str | None, pattern: re.Pattern) -> str:
    """Remove origin phrases, so the matcher cannot learn "origin = dangerous"."""
    cleaned = pattern.sub(" ", text or "")
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)  # no space before punctuation
    return re.sub(r"\s+", " ", cleaned).strip(" ,;-")


def alert_text(alert: dict, pattern: re.Pattern) -> str:
    """The alert as the index stores it: product, name, brand + model, description."""
    brand_model = " ".join(x for x in (alert.get("brand"), alert.get("model")) if x)
    parts = [alert.get("product"), alert.get("name"), brand_model, alert.get("description")]
    return strip_origin(". ".join(p for p in parts if p), pattern)


def listing_views(alert: dict, pattern: re.Pattern) -> list[tuple[str, str]]:
    """Listing-like texts of an alert: a seller-style title and the description."""
    title = " ".join(
        x for x in (alert.get("brand"), alert.get("name") or alert.get("product"),
                    alert.get("model")) if x)
    views = [("title", strip_origin(title, pattern)),
             ("description", strip_origin(alert.get("description"), pattern))]
    return [(kind, text) for kind, text in views if len(text.split()) >= 2]


def tokens(text: str | None) -> set[str]:
    words = re.findall(r"[a-z0-9à-ÿ]{3,}", norm(text))
    return {w for w in words if w not in STOPWORDS and not w.isdigit()}


def split_by_time(alerts: list[dict], test_days: int) -> tuple[list[dict], list[dict], int]:
    """Alerts of the last test_days days (counted from the newest alert) go to test.

    Alerts that are the same product (same brand + model, or a shared barcode) are one group,
    and a group goes to test as a whole when one of its alerts is recent, so the same product
    is never in train and test. Returns train, test and the number of alerts moved to test.
    """
    parent = {a["alert_id"]: a["alert_id"] for a in alerts}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    first_with = {}
    for alert in alerts:
        keys = [f"code:{b}" for b in alert.get("barcodes") or []]
        if alert.get("brand") and alert.get("model"):
            keys.append(f"product:{norm(alert['brand'])}|{norm(alert['model'])}")
        for key in keys:
            if key in first_with:
                parent[find(alert["alert_id"])] = find(first_with[key])
            else:
                first_with[key] = alert["alert_id"]

    dates = [a["publication_date"] for a in alerts if a.get("publication_date")]
    cutoff = (date.fromisoformat(max(dates)) - timedelta(days=test_days)).isoformat()
    recent = {a["alert_id"] for a in alerts if (a.get("publication_date") or "") > cutoff}
    test_groups = {find(a) for a in recent}
    test = [a for a in alerts if find(a["alert_id"]) in test_groups]
    train = [a for a in alerts if find(a["alert_id"]) not in test_groups]
    return train, test, len(test) - len(recent)


class ListingIndex:
    """Find ABO listings that share the most informative words with a text (rare words count
    more: inverse document frequency)."""

    def __init__(self, listings: list[dict], pattern: re.Pattern):
        self.listings = listings
        self.texts = [listing_text(x, pattern) for x in listings]
        postings = defaultdict(list)
        for i, text in enumerate(self.texts):
            for word in tokens(text):
                postings[word].append(i)
        max_df = max(MIN_DF_CAP, int(MAX_DF_SHARE * len(listings)))
        n = len(listings)
        self.postings = {w: ids for w, ids in postings.items() if len(ids) <= max_df}
        self.idf = {w: math.log(n / len(ids)) for w, ids in self.postings.items()}

    def similar(self, text: str, exclude_brand: str | None, limit: int = 50) -> list[int]:
        """Listing numbers, most similar first; listings of exclude_brand are left out."""
        scores = defaultdict(float)
        for word in tokens(text):
            for i in self.postings.get(word, []):
                scores[i] += self.idf[word]
        ranked = sorted(scores, key=lambda i: (-scores[i], i))
        brand = norm(exclude_brand)
        return [i for i in ranked if not brand or norm(self.listings[i].get("brand")) != brand][
            :limit]


def listing_text(listing: dict, pattern: re.Pattern) -> str:
    """An ABO listing as a matcher input: title plus the start of the description."""
    description = (listing.get("description") or "")[:300]
    return strip_origin(" ".join(x for x in (listing.get("title"), description) if x), pattern)


def build(alerts, listings, test_days=30, max_listings=30000, normal_listings=2000, seed=42):
    """All outputs as lists of dicts, plus counts for MLflow."""
    rng = random.Random(seed)
    pattern = origin_pattern({a["country_of_origin"] for a in alerts if a.get("country_of_origin")})
    train_alerts, test_alerts, moved = split_by_time(alerts, test_days)
    split_of = {a["alert_id"]: "train" for a in train_alerts} | {
        a["alert_id"]: "test" for a in test_alerts}

    shuffled = sorted(listings, key=lambda x: (x["item_id"], x.get("domain_name") or ""))
    rng.shuffle(shuffled)
    normal = shuffled[:normal_listings]  # test only: never used as a training negative
    index = ListingIndex(shuffled[normal_listings : normal_listings + max_listings], pattern)

    documents = [
        {"alert_id": a["alert_id"], "text": alert_text(a, pattern),
         "split": split_of[a["alert_id"]],
         "category": a.get("category"), "risk_types": a.get("risk_types") or [],
         "country_of_origin": a.get("country_of_origin"),
         "publication_date": a.get("publication_date")}
        for a in alerts
    ]
    text_of = {d["alert_id"]: d["text"] for d in documents}

    train, similar, uses = [], 0, defaultdict(int)
    for alert in train_alerts:
        query = " ".join(filter(None, (alert.get("product"), alert.get("name"),
                                       alert.get("description"))))
        # uses are counted per text: the same product can be listed in several marketplaces
        candidates = index.similar(query, alert.get("brand"))
        free = [i for i in candidates if uses[index.texts[i]] < MAX_NEGATIVE_USES]
        match = rng.choice(free[:TOP_CANDIDATES]) if free else None
        if match is not None:
            uses[index.texts[match]] += 1
            similar += 1
        negative = index.texts[match] if match is not None else rng.choice(index.texts)
        for view, text in listing_views(alert, pattern):
            train.append({"anchor": text, "positive": text_of[alert["alert_id"]],
                          "negative": negative, "alert_id": alert["alert_id"], "view": view,
                          "negative_source": "similar" if match is not None else "random"})

    test = [{"query": text, "alert_id": a["alert_id"], "label": 1, "view": view}
            for a in test_alerts for view, text in listing_views(a, pattern)]
    test += [{"query": listing_text(x, pattern), "alert_id": None, "label": 0, "view": "listing",
              "item_id": x["item_id"], "domain_name": x.get("domain_name")} for x in normal]

    stats = {
        "alerts_train": len(train_alerts), "alerts_test": len(test_alerts),
        "alerts_moved_to_test_as_twins": moved, "train_triplets": len(train),
        "train_alerts_with_similar_negative": similar,
        "test_positive_queries": sum(t["label"] for t in test),
        "test_normal_listings": len(normal), "negative_pool": len(index.listings),
    }
    return train, test, documents, stats


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(records: list[dict], folder: Path, name: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / name, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_metrics(stats: dict[str, int]) -> None:
    """Log the counts to MLflow when it is installed (it is in the Azure ML environment)."""
    try:
        import mlflow
    except ImportError:
        return
    mlflow.log_metrics({k: float(v) for k, v in stats.items()})


def main() -> None:
    parser = argparse.ArgumentParser(description="Build (listing, alert) pairs for the matcher.")
    parser.add_argument("--alerts", type=Path, required=True, help="validate_alerts output")
    parser.add_argument("--listings", type=Path, required=True, help="abo_listings folder")
    parser.add_argument("--test-days", type=int, default=30)
    parser.add_argument("--max-listings", type=int, default=30000, help="negative pool size")
    parser.add_argument("--normal-listings", type=int, default=2000, help="test listings")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--documents", type=Path, required=True)
    args = parser.parse_args()

    train, test, documents, stats = build(
        read_jsonl(args.alerts / "alerts.jsonl"), read_jsonl(args.listings / "listings.jsonl"),
        args.test_days, args.max_listings, args.normal_listings, args.seed)
    write_jsonl(train, args.train, "pairs.jsonl")
    write_jsonl(test, args.test, "pairs.jsonl")
    write_jsonl(documents, args.documents, "alerts.jsonl")
    log_metrics(stats)
    print("build_pairs:", json.dumps(stats))


if __name__ == "__main__":
    main()
