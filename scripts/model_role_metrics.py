"""Deterministic fixtures and target-specific metrics for model-role study 047."""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
import statistics
from collections import Counter, defaultdict
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression

TEV1_FAMILIES = ("equipment_binary", "software_category", "incident_ordinal")
DOMAINS = ("equipment", "software", "policy", "safety")
ITEM_IDS = tuple(f"E{n:02d}" for n in range(1, 9))


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def generate_tev1_cases(seed: int = 47060) -> list[dict[str, Any]]:
    """Return balanced, target-distinct Tev1 fixtures with hidden labels."""
    rng = random.Random(seed)
    cases: list[dict[str, Any]] = []
    binary_values = ("false", "true")
    fault_labels = (
        "null_dereference",
        "race_condition",
        "bad_serialization",
        "stale_cache",
    )
    fault_text = {
        "null_dereference": "The trace reaches an absent object field before the crash.",
        "race_condition": "Two workers write the same value; the outcome changes with timing.",
        "bad_serialization": "The parser rejects a field whose encoded type does not match the schema.",
        "stale_cache": "A repeated read returns the earlier value after the record was updated.",
    }
    severity_labels = ("routine", "limited", "major", "critical")
    severity_text = {
        "routine": "One nonessential service is delayed; no user action is blocked.",
        "limited": "A small user group has a workaround and no data is lost.",
        "major": "A core service is unavailable to many users, but data remains intact.",
        "critical": "Multiple core services fail and confirmed data loss is ongoing.",
    }
    for family in TEV1_FAMILIES:
        labels = (
            binary_values
            if family == TEV1_FAMILIES[0]
            else (fault_labels if family == TEV1_FAMILIES[1] else severity_labels)
        )
        per_label = 32 if len(labels) == 2 else 16
        for label in labels:
            for index in range(per_label):
                split = "development" if index < per_label // 2 else "heldout"
                variant = rng.randrange(10000)
                if family == TEV1_FAMILIES[0]:
                    state = (
                        f"Equipment log {variant}: unit K-{variant % 97:02d} had a "
                        f"vibration reading of {7.1 if label == 'true' else 1.2} mm/s; "
                        f"the alarm threshold is 5.0 mm/s. The bearing inspection "
                        f"{'found a fractured race' if label == 'true' else 'found no damage'}; "
                        "the maintenance note is preliminary."
                    )
                    question = {
                        "type": "noul",
                        "instructions": "Is the named bearing fault present in the record?",
                        "criteria": {
                            "true": "The record supports that the bearing fault is present.",
                            "false": "The record supports that the bearing fault is absent.",
                        },
                    }
                elif family == TEV1_FAMILIES[1]:
                    state = f"Software test {variant}: {fault_text[label]}"
                    question = {
                        "type": "choice",
                        "instructions": "Which defect class best explains the observed behavior?",
                        "criteria": {key: fault_text[key] for key in fault_labels},
                    }
                else:
                    state = f"Incident report {variant}: {severity_text[label]}"
                    question = {
                        "type": "score",
                        "instructions": "Score the incident severity from the report.",
                        "criteria": [severity_text[key] for key in severity_labels],
                    }
                cases.append(
                    {
                        "case_id": f"{family}-{label}-{index:02d}",
                        "family": family,
                        "split": split,
                        "state": state,
                        "question": question,
                        "class_labels": list(labels),
                        "gold_label": label,
                    }
                )
    return cases


def generate_relevance_cases(seed: int = 47061) -> list[dict[str, Any]]:
    """Return balanced synthetic query/evidence pools; labels stay outside prompts."""
    rng = random.Random(seed)
    cases: list[dict[str, Any]] = []
    for domain in DOMAINS:
        for n in range(32):
            query_id = f"{domain}-Q{n:02d}"
            topic = rng.randrange(10000)
            query_text = {
                "equipment": f"Did inspection {topic} confirm a bearing fault on unit K-{n:02d}?",
                "software": f"Which defect caused test {topic} to return the wrong value?",
                "policy": f"Does request {topic} meet the stated return-window rule?",
                "safety": f"Does event {topic} show that a guard was bypassed during operation?",
            }[domain]
            split = "development" if n < 16 else "heldout"
            primary = f"Record {topic}: the inspected unit's measured condition directly answers query {topic}."
            item_texts = [
                primary,
                f"Record {topic}-B: a second direct measurement bears on the same question {topic}.",
                f"Record {topic}-C: the same subject is mentioned, but it does not resolve question {topic}.",
                f"Record {topic}-D: a similar event on another unit could mislead about {topic}.",
                primary + " This is a duplicate copy from the same upstream record.",
                f"Record {topic}-F: a routine status unrelated to the queried outcome {topic}.",
                f"Record {topic}-G: a general procedure note with no observation about {topic}.",
                f"Record {topic}-H: unrelated background text from a different case than {topic}.",
            ]
            labels = [True, True, False, False, True, False, False, False]
            items = []
            for item_id, text, relevant in zip(
                ITEM_IDS, item_texts, labels, strict=True
            ):
                items.append(
                    {
                        "item_id": item_id,
                        "text": text,
                        "relevant": relevant,
                        "source_status": "verified"
                        if item_id in {"E01", "E02"}
                        else "unknown",
                        "operation_use": relevant and item_id == "E01",
                    }
                )
            cases.append(
                {
                    "query_id": query_id,
                    "domain": domain,
                    "split": split,
                    "query": query_text,
                    "items": items,
                }
            )
    return cases


def parse_chat_items(content: str, item_ids: Sequence[str]) -> list[dict[str, Any]]:
    value = json.loads(content)
    items = value.get("items") if isinstance(value, dict) else None
    if not isinstance(items, list):
        raise ValueError("model output must have an items list")
    parsed: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each model item must be an object")
        item_id = item.get("item_id")
        relevant = item.get("relevant")
        probability = item.get("probability")
        if item_id not in item_ids or item_id in parsed or type(relevant) is not bool:
            raise ValueError(
                "model output has an unknown/duplicate ID or invalid label"
            )
        if isinstance(probability, bool) or not isinstance(probability, (int, float)):
            raise ValueError("model probability must be numeric")
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError("model probability must be between 0 and 1")
        parsed[item_id] = {
            "item_id": item_id,
            "label": relevant,
            "raw_score": float(probability),
            "score_type": "self_reported_relevance_probability",
        }
    if set(parsed) != set(item_ids):
        raise ValueError("model output is missing candidate IDs")
    return [parsed[item_id] for item_id in item_ids]


def parse_guardian_score(content: str) -> dict[str, Any]:
    """Parse the documented single-item Guardian `<score>yes/no</score>` output."""
    match = re.fullmatch(r"\s*<score>\s*(yes|no)\s*</score>\s*", content, re.IGNORECASE)
    if match is None:
        raise ValueError("Guardian output is not one documented yes/no score")
    label = match.group(1).lower() == "yes"
    return {
        "label": label,
        "raw_score": 1.0 if label else 0.0,
        "score_type": "binary_critic_judgment",
    }


def _valid(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in rows if r.get("valid", True) and r.get("probs") is not None]


def _binary_auc(labels: Sequence[int], scores: Sequence[float]) -> float | None:
    positives = [
        score for label, score in zip(labels, scores, strict=True) if label == 1
    ]
    negatives = [
        score for label, score in zip(labels, scores, strict=True) if label == 0
    ]
    if not positives or not negatives:
        return None
    comparisons = [
        1.0 if p > n else 0.5 if p == n else 0.0 for p in positives for n in negatives
    ]
    return sum(comparisons) / len(comparisons)


def _auc(labels: Sequence[int], matrix: np.ndarray) -> float | None:
    classes = sorted(set(int(label) for label in labels))
    if len(classes) < 2:
        return None
    if matrix.shape[1] == 2:
        return _binary_auc(labels, matrix[:, 1].tolist())
    values = []
    for target in range(matrix.shape[1]):
        scores = [float(row[target]) for row in matrix]
        binary = [int(label == target) for label in labels]
        area = _binary_auc(binary, scores)
        if area is not None:
            values.append(area)
    return sum(values) / len(values) if values else None


def _point_metric(
    probs: Sequence[Sequence[float]], labels: Sequence[int], key: str
) -> float | None:
    if not labels:
        return None
    matrix = np.asarray(probs, dtype=float)
    y = np.asarray(labels, dtype=int)
    matrix = np.clip(matrix, 1e-12, 1.0)
    matrix /= matrix.sum(axis=1, keepdims=True)
    if key == "brier":
        one_hot = np.eye(matrix.shape[1])[y]
        return float(np.square(matrix - one_hot).sum(axis=1).mean())
    if key == "log_loss":
        return float(-np.log(matrix[np.arange(len(y)), y]).mean())
    if key == "auc":
        return _auc(y.tolist(), matrix)
    raise ValueError(f"unsupported metric: {key}")


def _calibration(
    probs: Sequence[Sequence[float]], labels: Sequence[int], bins: int = 5
) -> dict[str, Any]:
    if not labels:
        return {"brier": None, "log_loss": None, "ece": None, "reliability_bins": []}
    matrix = np.asarray(probs, dtype=float)
    y = np.asarray(labels, dtype=int)
    matrix = np.clip(matrix, 1e-12, 1.0)
    matrix = matrix / matrix.sum(axis=1, keepdims=True)
    one_hot = np.eye(matrix.shape[1])[y]
    top = matrix.argmax(axis=1)
    confidence = matrix.max(axis=1)
    correct = (top == y).astype(float)
    edges = np.linspace(0, 1, bins + 1)
    reliability = []
    ece = 0.0
    for i in range(bins):
        mask = (confidence >= edges[i]) & (
            confidence <= edges[i + 1] if i == bins - 1 else confidence < edges[i + 1]
        )
        count = int(mask.sum())
        accuracy = float(correct[mask].mean()) if count else None
        mean_confidence = float(confidence[mask].mean()) if count else None
        if count:
            ece += count / len(y) * abs(accuracy - mean_confidence)
        reliability.append(
            {
                "lower": float(edges[i]),
                "upper": float(edges[i + 1]),
                "count": count,
                "accuracy": accuracy,
                "mean_confidence": mean_confidence,
            }
        )
    loss = _point_metric(matrix, y.tolist(), "log_loss")
    auc = _point_metric(matrix, y.tolist(), "auc")
    return {
        "count": len(y),
        "brier": float(np.square(matrix - one_hot).sum(axis=1).mean()),
        "log_loss": loss,
        "expected_calibration_error": float(ece),
        "auc": auc,
        "accuracy": float((top == y).mean()),
        "reliability_bins": reliability,
    }


def _bootstrap_ci(
    rows: Sequence[dict[str, Any]],
    metric: Callable[[list[dict[str, Any]]], float | None],
    seed: int,
    replicates: int = 2000,
) -> list[float] | None:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for i, row in enumerate(rows):
        groups[str(row.get("query_id", row.get("case_id", i)))].append(row)
    keys = list(groups)
    if not keys:
        return None
    rng = random.Random(seed)
    values = []
    for _ in range(replicates):
        sample = [r for key in (rng.choice(keys) for _ in keys) for r in groups[key]]
        value = metric(sample)
        if value is not None and math.isfinite(value):
            values.append(value)
    if not values:
        return None
    return [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]


def tev1_calibration_metrics(
    rows: Sequence[dict[str, Any]], seed: int = 47062
) -> dict[str, Any]:
    valid = _valid(rows)
    if not valid:
        return {**_calibration([], []), "count": 0, "invalid_count": len(rows)}
    labels = [int(r["gold_index"]) for r in valid]
    probs = [r["probs"] for r in valid]
    metrics = _calibration(probs, labels)
    for key in ("brier", "log_loss", "auc"):
        metrics.setdefault("uncertainty_95", {})[key] = _bootstrap_ci(
            valid,
            lambda sample: _point_metric(
                [r["probs"] for r in sample],
                [int(r["gold_index"]) for r in sample],
                key,
            ),
            seed,
        )
    if len(probs[0]) > 2:
        cumulative = []
        for threshold in range(len(probs[0]) - 1):
            binary_probs = [sum(p[threshold + 1 :]) for p in probs]
            binary_rows = [
                {
                    "query_id": r.get("case_id"),
                    "p": p,
                    "y": int(r["gold_index"] > threshold),
                }
                for r, p in zip(valid, binary_probs, strict=True)
            ]
            brier = float(np.mean([(r["p"] - r["y"]) ** 2 for r in binary_rows]))
            cumulative.append({"threshold": threshold, "brier": brier})
        metrics["ordinal_threshold_calibration"] = cumulative
        metrics["ranked_probability_score"] = float(
            np.mean(
                [
                    np.square(
                        np.cumsum(p)[:-1]
                        - (np.arange(len(p) - 1) >= r["gold_index"]).astype(float)
                    ).mean()
                    for p, r in zip(probs, valid, strict=True)
                ]
            )
        )
    metrics["invalid_count"] = len(rows) - len(valid)
    metrics["class_counts"] = dict(Counter(str(r["gold_label"]) for r in rows))
    metrics["class_proportions"] = (
        {label: count / len(rows) for label, count in metrics["class_counts"].items()}
        if rows
        else {}
    )
    if set(metrics["class_counts"]) == {"false", "true"}:
        metrics["event_rate"] = metrics["class_proportions"]["true"]
    return metrics


def fit_calibration(dev_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    valid = [
        r for r in dev_rows if r.get("valid", True) and r.get("raw_score") is not None
    ]
    labels = [int(r["gold"]) for r in valid]
    if len(set(labels)) < 2:
        return {"available": False, "reason": "development split lacks both classes"}
    model = LogisticRegression(
        C=1.0, solver="liblinear", max_iter=1000, random_state=47063
    )
    model.fit(
        np.asarray([float(r["raw_score"]) for r in valid]).reshape(-1, 1),
        np.asarray(labels),
    )
    return {
        "available": True,
        "intercept": float(model.intercept_[0]),
        "coefficient": float(model.coef_[0][0]),
        "development_count": len(valid),
    }


def apply_calibration(score: float, calibration: dict[str, Any]) -> float | None:
    if not calibration.get("available"):
        return None
    z = calibration["intercept"] + calibration["coefficient"] * score
    return 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, z))))


def relevance_metrics(
    rows: Sequence[dict[str, Any]], seed: int = 47064
) -> dict[str, Any]:
    valid = [
        r
        for r in rows
        if r.get("valid") and r.get("calibrated_probability") is not None
    ]
    if not valid:
        return {"count": 0, "invalid_count": len(rows), "metrics": _calibration([], [])}
    metric_rows = [
        {
            "query_id": r["query_id"],
            "gold_index": int(r["gold"]),
            "probs": [1.0 - r["calibrated_probability"], r["calibrated_probability"]],
        }
        for r in valid
    ]
    summary = _calibration(
        [r["probs"] for r in metric_rows], [r["gold_index"] for r in metric_rows]
    )
    summary["invalid_count"] = len(rows) - len(valid)
    summary["query_count"] = len({r["query_id"] for r in valid})
    summary["event_rate"] = float(np.mean([r["gold"] for r in valid]))
    summary["uncertainty_95"] = {
        key: _bootstrap_ci(
            metric_rows,
            lambda sample: _point_metric(
                [r["probs"] for r in sample], [r["gold_index"] for r in sample], key
            ),
            seed + n,
        )
        for n, key in enumerate(("brier", "log_loss", "auc"))
    }
    return summary


def binary_decision_metrics(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    valid = [
        r
        for r in rows
        if r.get("valid") and r.get("calibrated_probability") is not None
    ]
    tp = fp = tn = fn = 0
    for row in valid:
        predicted = float(row["calibrated_probability"]) >= 0.5
        actual = bool(row["gold"])
        tp += int(predicted and actual)
        fp += int(predicted and not actual)
        tn += int(not predicted and not actual)
        fn += int(not predicted and actual)
    return {
        "count": len(valid),
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "false_positive_rate": fp / (fp + tn) if fp + tn else None,
        "false_negative_rate": fn / (fn + tp) if fn + tp else None,
    }


def raw_score_auc(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    valid = [r for r in rows if r.get("valid") and r.get("raw_score") is not None]
    area = _binary_auc(
        [int(r["gold"]) for r in valid], [float(r["raw_score"]) for r in valid]
    )
    return {"count": len(valid), "auc": area}


def ranking_metrics(
    rows: Sequence[dict[str, Any]],
    score_key: str = "raw_score",
    seed: int = 47065,
    replicates: int = 2000,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get(score_key) is not None:
            grouped[row["query_id"]].append(row)
    complete = []
    tops = {}
    for query_id, items in grouped.items():
        if len(items) != len(ITEM_IDS) or any(not row.get("valid") for row in items):
            continue
        ranked = sorted(items, key=lambda r: (-float(r[score_key]), r["item_id"]))
        tops[query_id] = ranked[0]["item_id"] if ranked else None
        complete.append(items)

    def query_scores(items: list[dict[str, Any]]) -> tuple[float, dict[int, float]]:
        ranked = sorted(items, key=lambda r: (-float(r[score_key]), r["item_id"]))
        relevant = {r["item_id"] for r in items if r["gold"]}
        ranks = [i + 1 for i, row in enumerate(ranked) if row["item_id"] in relevant]
        reciprocal = 1.0 / min(ranks) if ranks else 0.0
        recalls = {
            k: len({r["item_id"] for r in ranked[:k]} & relevant)
            / max(1, len(relevant))
            for k in (1, 3, 5)
        }
        return reciprocal, recalls

    observed = [query_scores(items) for items in complete]
    uncertainty = {"mrr": None, "recall_at_k": {str(k): None for k in (1, 3, 5)}}
    if complete:
        rng = random.Random(seed)
        mrr_draws = []
        recall_draws = {k: [] for k in (1, 3, 5)}
        for _ in range(replicates):
            values = [rng.choice(observed) for _ in observed]
            mrr_draws.append(statistics.mean(value[0] for value in values))
            for k in recall_draws:
                recall_draws[k].append(statistics.mean(value[1][k] for value in values))
        uncertainty = {
            "mrr": [
                float(np.quantile(mrr_draws, 0.025)),
                float(np.quantile(mrr_draws, 0.975)),
            ],
            "recall_at_k": {
                str(k): [
                    float(np.quantile(draws, 0.025)),
                    float(np.quantile(draws, 0.975)),
                ]
                for k, draws in recall_draws.items()
            },
        }
    return {
        "query_count": len(grouped),
        "ranked_query_count": len(tops),
        "incomplete_query_count": len(grouped) - len(tops),
        "query_coverage": len(tops) / len(grouped) if grouped else 0.0,
        "mrr": statistics.mean(value[0] for value in observed) if observed else None,
        "recall_at_k": {
            str(k): statistics.mean(value[1][k] for value in observed)
            if observed
            else None
            for k in (1, 3, 5)
        },
        "uncertainty_95": uncertainty,
        "top_item_by_query": tops,
    }


def calibration_by_domain(
    dev_rows: Sequence[dict[str, Any]], test_rows: Sequence[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fitted = fit_calibration(dev_rows)
    scored = []
    for row in test_rows:
        copy = dict(row)
        copy["calibrated_probability"] = (
            apply_calibration(float(row["raw_score"]), fitted)
            if row.get("valid") and row.get("raw_score") is not None
            else None
        )
        scored.append(copy)
    return fitted, scored
