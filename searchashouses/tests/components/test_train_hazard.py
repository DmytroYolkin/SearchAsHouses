"""Unit tests for the train_hazard labels and thresholds (#24). Standard library only, no torch."""

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]  # searchashouses/
sys.path.insert(0, str(PROJECT / "azureml" / "components" / "train_hazard" / "src"))
import hazard_labels as hl  # noqa: E402


def records(counts: dict) -> list[dict]:
    """counts {risk type: number of alerts} -> one single-label alert per count."""
    return [{"risk_types": [risk]} for risk, n in counts.items() for _ in range(n)]


def test_rare_risk_types_are_grouped_into_other():
    data = records({"Chemical": 60, "Choking": 50, "Explosion": 7, "Abrasion": 1})
    labels, mapping = hl.label_map(data, min_alerts=50)
    assert labels == ["Chemical", "Choking", hl.OTHER_LABEL]
    assert mapping["Explosion"] == mapping["Abrasion"] == hl.OTHER_LABEL
    assert mapping["Choking"] == "Choking"  # exactly min_alerts is enough


def test_risk_types_become_a_multi_label_target():
    labels, mapping = hl.label_map(records({"Chemical": 60, "Choking": 60, "Explosion": 1}))
    assert hl.encode(["Choking", "Chemical"], labels, mapping) == [1, 1, 0]
    assert hl.encode(["Explosion"], labels, mapping) == [0, 0, 1]
    assert hl.encode(["Never seen before"], labels, mapping) == [0, 0, 1]
    assert hl.encode([], labels, mapping) == [0, 0, 0]


def test_rare_labels_get_a_larger_class_weight():
    targets = [[1, 0]] * 50 + [[1, 1]] * 1 + [[0, 0]] * 49  # label 0: 51 of 100, label 1: 1
    common, rare = hl.pos_weights(targets)
    assert round(common, 2) == round((49 / 51) ** 0.5, 2)  # about 1: no extra weight
    assert rare == min(hl.MAX_POS_WEIGHT, 99**0.5)  # sqrt(99 negatives / 1 positive)
    assert hl.pos_weights([[1, 0]] * 2000)[1] == hl.MAX_POS_WEIGHT  # never positive: the cap


def test_threshold_is_chosen_for_the_best_f1():
    # Positives score 0.30-0.40, negatives 0.10-0.20: 0.5 misses them all, 0.25 is perfect.
    scores = [0.30, 0.32, 0.35, 0.38, 0.40, 0.10, 0.12, 0.15, 0.18, 0.20]
    truth = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    assert hl.f1(scores, truth, 0.5) == 0.0
    threshold = hl.best_threshold(scores, truth)
    assert hl.f1(scores, truth, threshold) == 1.0
    assert threshold == 0.30  # of the perfect thresholds (0.25 and 0.30), the one nearest 0.5


def test_too_few_positives_keep_the_default_threshold():
    scores = [0.3, 0.1, 0.1, 0.1]
    assert hl.best_threshold(scores, [1, 0, 0, 0]) == hl.DEFAULT_THRESHOLD


def test_thresholds_and_scores_per_label():
    labels = ["A", "B"]
    probs = [[0.9, 0.35]] * 5 + [[0.1, 0.05]] * 5
    targets = [[1, 1]] * 5 + [[0, 0]] * 5
    thresholds = hl.choose_thresholds(probs, targets)
    assert thresholds[0] == 0.5 and 0.05 < thresholds[1] <= 0.35  # B needs a lower threshold
    result = hl.scores(probs, targets, thresholds, labels)
    assert result == {"per_label_f1": {"A": 1.0, "B": 1.0}, "macro_f1": 1.0}
    assert hl.scores(probs, targets, [0.5, 0.5], labels)["macro_f1"] == 0.5  # B: F1 0 at 0.5


def test_validation_split_is_by_alert_and_repeatable():
    data = [{"alert_id": i} for i in range(100)]
    train, val = hl.split_validation(data, share=0.15, seed=42)
    assert len(val) == 15 and len(train) == 85
    assert not {r["alert_id"] for r in train} & {r["alert_id"] for r in val}
    assert hl.split_validation(data, share=0.15, seed=42) == (train, val)
