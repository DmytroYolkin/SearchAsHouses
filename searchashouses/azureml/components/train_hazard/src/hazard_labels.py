"""Labels, class weights and thresholds for the hazard classifier (#24). Standard library only.

Kept apart from train_hazard.py (which needs torch), so the unit tests run in CI without torch.
"""

import math
import random

OTHER_LABEL = "Health risk / other"  # Safety Gate's own catch-all risk type
MIN_ALERTS = 50  # a risk type with fewer training alerts goes into OTHER_LABEL (decided in #17)
MAX_POS_WEIGHT = 30.0  # upper limit of the class weight of a very rare risk type
MIN_VAL_POSITIVES = 5  # fewer positives in validation: keep the default threshold
DEFAULT_THRESHOLD = 0.5
THRESHOLD_GRID = [round(0.05 * i, 2) for i in range(1, 20)]  # 0.05, 0.10, ..., 0.95


def label_map(records: list[dict], min_alerts: int = MIN_ALERTS) -> tuple[list[str], dict]:
    """Return the classifier labels and a map from every risk type to its label.

    A risk type with fewer than min_alerts alerts is too rare to learn on its own; it is counted
    as OTHER_LABEL. Labels are sorted, so the same data always gives the same label order.
    """
    counts: dict[str, int] = {}
    for record in records:
        for risk in set(record["risk_types"]):
            counts[risk] = counts.get(risk, 0) + 1
    mapping = {risk: risk if n >= min_alerts else OTHER_LABEL for risk, n in counts.items()}
    return sorted(set(mapping.values())), mapping


def encode(risk_types: list[str], labels: list[str], mapping: dict) -> list[int]:
    """Multi-label target: 1 for every label of the alert, 0 for the others.

    An unknown risk type (not seen in training) counts as OTHER_LABEL when that label exists.
    """
    fallback = OTHER_LABEL if OTHER_LABEL in labels else None
    wanted = {mapping.get(risk, fallback) for risk in risk_types}
    return [1 if label in wanted else 0 for label in labels]


def split_validation(records: list, share: float, seed: int) -> tuple[list, list]:
    """Random split by alert: (train, validation). The validation part picks the thresholds."""
    shuffled = list(records)
    random.Random(seed).shuffle(shuffled)
    n_val = round(len(shuffled) * share)
    return shuffled[n_val:], shuffled[:n_val]


def pos_weights(targets: list[list[int]]) -> list[float]:
    """Class weight per label for the loss: sqrt(negatives / positives), at most MAX_POS_WEIGHT.

    Without it the model learns that predicting "no" is almost always right for a rare risk type.
    The square root softens the weight: the thresholds are tuned afterwards anyway.
    """
    n = len(targets)
    weights = []
    for j in range(len(targets[0])):
        positives = sum(t[j] for t in targets)
        ratio = (n - positives) / positives if positives else MAX_POS_WEIGHT**2
        weights.append(min(MAX_POS_WEIGHT, math.sqrt(ratio)))
    return weights


def f1(scores: list[float], truth: list[int], threshold: float) -> float:
    """F1 of one label when every score >= threshold counts as "yes"."""
    tp = fp = fn = 0
    for score, actual in zip(scores, truth):
        predicted = score >= threshold
        if predicted and actual:
            tp += 1  # true positive
        elif predicted:
            fp += 1  # false positive
        elif actual:
            fn += 1  # missed (false negative)
    return 2 * tp / (2 * tp + fp + fn) if tp else 0.0


def best_threshold(scores: list[float], truth: list[int]) -> float:
    """The threshold on THRESHOLD_GRID with the best F1 for one label.

    A tie goes to the threshold closest to 0.5. With fewer than MIN_VAL_POSITIVES positives the
    F1 is too noisy to choose from, so the default 0.5 is kept.
    """
    if sum(truth) < MIN_VAL_POSITIVES:
        return DEFAULT_THRESHOLD
    return max(THRESHOLD_GRID, key=lambda t: (f1(scores, truth, t), -abs(t - DEFAULT_THRESHOLD)))


def columns(matrix: list[list]) -> list[list]:
    """Rows (one per alert) to columns (one per label)."""
    return [list(column) for column in zip(*matrix)]


def choose_thresholds(probs: list[list[float]], targets: list[list[int]]) -> list[float]:
    """One threshold per label, picked on the validation predictions."""
    return [best_threshold(s, t) for s, t in zip(columns(probs), columns(targets))]


def scores(probs, targets, thresholds, labels) -> dict:
    """F1 per label and macro-F1 (the plain mean over labels, so rare risk types count fully)."""
    per_label = {label: f1(s, t, th) for label, s, t, th
                 in zip(labels, columns(probs), columns(targets), thresholds)}
    return {"per_label_f1": per_label, "macro_f1": sum(per_label.values()) / len(per_label)}
