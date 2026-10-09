"""Evaluate frozen public-only operation-policy cases and score them separately."""

from __future__ import annotations

import hashlib
import json
import random
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PATH = ROOT / "docs/experiments/operation-policy-challenge-v2-public.jsonl"
EVALUATOR_PATH = ROOT / "docs/experiments/operation-policy-challenge-v2-evaluator.jsonl"
PREREG_PATH = (
    ROOT / "docs/research/operation-specific-policy-validation-preregistration.md"
)
RESULT_PATH = ROOT / "docs/experiments/operation-policy-challenge-v2-results.json"
POLICIES = (
    "naive_aggregation",
    "global_label",
    "metadata_only",
    "operation_specific",
)
BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 4701
PUBLIC_CASE_KEYS = {"case_id", "operation", "left", "right", "context"}
PUBLIC_SOURCE_KEYS = {
    "source_id",
    "target_id",
    "event_id",
    "observation_process",
    "observation_window",
    "score",
    "score_semantics",
    "model_revision",
    "source_status",
    "lineage_group",
    "conflict",
    "calibration",
    "mapped_score",
    "global_label",
}
PUBLIC_CONTEXT_KEYS = {
    "decision_threshold",
    "mixture_estimand",
    "weights",
    "ranking_estimand",
    "claim_id",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_public_case(case: dict[str, Any]) -> None:
    if set(case) != PUBLIC_CASE_KEYS:
        raise ValueError(
            "candidate input has fields outside the frozen public case schema"
        )
    for source_name in ("left", "right"):
        source = case[source_name]
        if not isinstance(source, dict) or set(source) != PUBLIC_SOURCE_KEYS:
            raise ValueError(
                "candidate source has fields outside the frozen public schema"
            )
        calibration = source["calibration"]
        if calibration is not None and (
            not isinstance(calibration, dict)
            or set(calibration) != {"target_id", "model_revision", "split"}
        ):
            raise ValueError(
                "candidate calibration has fields outside the frozen public schema"
            )
    context = case["context"]
    if not isinstance(context, dict) or not set(context).issubset(PUBLIC_CONTEXT_KEYS):
        raise ValueError(
            "candidate context has fields outside the frozen public schema"
        )


def _metadata_match(left: dict[str, Any], right: dict[str, Any]) -> bool:
    required = (
        "target_id",
        "event_id",
        "observation_process",
        "observation_window",
        "score_semantics",
        "model_revision",
    )
    return (
        all(
            left.get(key) is not None and left.get(key) == right.get(key)
            for key in required
        )
        and left.get("source_status") == right.get("source_status") == "verified"
        and left.get("lineage_group") is not None
        and right.get("lineage_group") is not None
        and left["lineage_group"] != right["lineage_group"]
    )


def _calibration_fits(source: dict[str, Any], target_id: str) -> bool:
    calibration = source.get("calibration")
    return (
        isinstance(calibration, dict)
        and calibration.get("target_id") == target_id
        and calibration.get("model_revision") == source.get("model_revision")
        and calibration.get("split") == "development"
    )


def _operation_specific(case: dict[str, Any]) -> bool:
    left, right = case["left"], case["right"]
    context = case.get("context", {})
    if (
        left.get("source_status") != "verified"
        or right.get("source_status") != "verified"
    ):
        return False

    operation = case["operation"]
    if operation == "forecast_pool":
        if left.get("observation_process") != right.get("observation_process"):
            return False
        if left.get("observation_window") != right.get("observation_window"):
            return False
        if any(
            source.get("score_semantics") != "probability" for source in (left, right)
        ):
            return False
        if not all(
            _calibration_fits(source, source.get("target_id"))
            for source in (left, right)
        ):
            return False
        same_target = left.get("target_id") == right.get("target_id") and left.get(
            "event_id"
        ) == right.get("event_id")
        if same_target:
            return True
        weights = context.get("weights")
        return (
            isinstance(context.get("mixture_estimand"), str)
            and bool(context["mixture_estimand"])
            and isinstance(weights, list)
            and len(weights) == 2
            and all(_number(weight) and weight >= 0 for weight in weights)
            and abs(sum(weights) - 1.0) <= 1e-9
        )

    if operation == "relevance_rank":
        target = context.get("ranking_estimand")
        return (
            isinstance(target, str)
            and left.get("target_id") == right.get("target_id") == target
            and left.get("event_id") == right.get("event_id")
            and _number(left.get("mapped_score"))
            and _number(right.get("mapped_score"))
            and _calibration_fits(left, target)
            and _calibration_fits(right, target)
        )

    if operation == "evidence_combine":
        left_lineage, right_lineage = (
            left.get("lineage_group"),
            right.get("lineage_group"),
        )
        return (
            isinstance(context.get("claim_id"), str)
            and left.get("target_id") == right.get("target_id") == context["claim_id"]
            and left_lineage is not None
            and right_lineage is not None
            and left_lineage != right_lineage
            and left.get("conflict") is False
            and right.get("conflict") is False
        )
    return False


def candidate_permission(policy: str, case: dict[str, Any]) -> tuple[bool, int]:
    """Return a public-input decision and its declared rule-check count."""
    left, right = case["left"], case["right"]
    if policy == "naive_aggregation":
        return True, 0
    if policy == "global_label":
        a, b = left.get("global_label"), right.get("global_label")
        return isinstance(a, str) and bool(a) and a == b, 1
    if policy == "metadata_only":
        return _metadata_match(left, right), 8
    if policy == "operation_specific":
        return _operation_specific(case), 12
    raise ValueError(f"unknown candidate policy: {policy}")


def _rank(case: dict[str, Any], policy: str) -> list[str] | None:
    if case["operation"] != "relevance_rank":
        return None
    score_key = "mapped_score" if policy == "operation_specific" else "score"
    ranked = sorted(
        (case["left"], case["right"]),
        key=lambda source: (source.get(score_key, float("-inf")), source["source_id"]),
        reverse=True,
    )
    return [source["source_id"] for source in ranked]


def _decision(case: dict[str, Any], policy: str) -> bool | None:
    context = case.get("context", {})
    threshold = context.get("decision_threshold")
    if case["operation"] != "forecast_pool" or not _number(threshold):
        return None
    values = [case["left"].get("score"), case["right"].get("score")]
    if not all(_number(value) for value in values):
        return None
    weights = context.get("weights")
    if (
        policy == "operation_specific"
        and context.get("mixture_estimand")
        and isinstance(weights, list)
        and len(weights) == 2
    ):
        value = sum(
            score * weight for score, weight in zip(values, weights, strict=True)
        )
    else:
        value = sum(values) / 2
    return value >= threshold


def candidate_outputs(
    public_cases: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Score candidate rules using public cases only; no evaluator data is accepted."""
    for case in public_cases:
        _validate_public_case(case)
    output: dict[str, list[dict[str, Any]]] = {}
    for policy in POLICIES:
        records = []
        for case in public_cases:
            allowed, checks = candidate_permission(policy, case)
            records.append(
                {
                    "case_id": case["case_id"],
                    "permission": allowed,
                    "ranking": _rank(case, policy) if allowed else None,
                    "decision": _decision(case, policy) if allowed else None,
                    "rule_checks": checks,
                    "model_calls": 0,
                    "public_metadata_bytes": len(
                        json.dumps(case, sort_keys=True, separators=(",", ":")).encode()
                    ),
                }
            )
        output[policy] = records
    return output


def _oracle_outputs(evaluator: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": row["case_id"],
            "permission": row["expected_permission"],
            "ranking": row["expected_ranking"],
            "decision": row["expected_decision"],
            "rule_checks": 0,
            "model_calls": 0,
            "public_metadata_bytes": 0,
        }
        for row in evaluator
    ]


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _bootstrap_difference(
    policy_values: list[float], baseline_values: list[float], seed: int
) -> dict[str, float | None]:
    paired = [a - b for a, b in zip(policy_values, baseline_values, strict=True)]
    if not paired:
        return {"difference": None, "low_95": None, "high_95": None}
    rng = random.Random(seed)
    means = [
        sum(rng.choice(paired) for _ in paired) / len(paired)
        for _ in range(BOOTSTRAP_RESAMPLES)
    ]
    means.sort()
    return {
        "difference": sum(paired) / len(paired),
        "low_95": means[int(0.025 * BOOTSTRAP_RESAMPLES)],
        "high_95": means[int(0.975 * BOOTSTRAP_RESAMPLES)],
    }


def summarize(
    public_cases: list[dict[str, Any]],
    evaluator: list[dict[str, Any]],
    outputs: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    labels = {row["case_id"]: row for row in evaluator}
    public = {row["case_id"]: row for row in public_cases}
    outputs["evaluator_oracle"] = _oracle_outputs(evaluator)
    by_policy = {
        name: {row["case_id"]: row for row in rows} for name, rows in outputs.items()
    }
    summaries: dict[str, Any] = {}
    families = sorted({case["operation"] for case in public_cases})

    for family in families:
        ids = [
            case_id for case_id, case in public.items() if case["operation"] == family
        ]
        valid_ids = [
            case_id for case_id in ids if labels[case_id]["expected_permission"]
        ]
        invalid_ids = [
            case_id for case_id in ids if not labels[case_id]["expected_permission"]
        ]
        ranking_ids = [
            case_id
            for case_id in ids
            if public[case_id].get("context", {}).get("ranking_estimand")
        ]
        decision_ids = [
            case_id
            for case_id in ids
            if "decision_threshold" in public[case_id].get("context", {})
        ]
        family_summary: dict[str, Any] = {"n_cases": len(ids), "policies": {}}
        for policy, records in by_policy.items():
            false_permissions = sum(
                records[case_id]["permission"] for case_id in invalid_ids
            )
            unnecessary_refusals = sum(
                not records[case_id]["permission"] for case_id in valid_ids
            )
            eligible_decisions = [
                case_id
                for case_id in ids
                if labels[case_id]["expected_decision"] is not None
                and records[case_id]["decision"] is not None
            ]
            decision_errors = sum(
                records[case_id]["decision"] != labels[case_id]["expected_decision"]
                for case_id in eligible_decisions
            )
            eligible_rankings = [
                case_id
                for case_id in ids
                if labels[case_id]["expected_ranking"] is not None
                and records[case_id]["ranking"] is not None
            ]
            ranking_errors = sum(
                records[case_id]["ranking"] != labels[case_id]["expected_ranking"]
                for case_id in eligible_rankings
            )
            family_summary["policies"][policy] = {
                "false_permissions": false_permissions,
                "false_permission_denominator": len(invalid_ids),
                "false_permission_rate": _rate(false_permissions, len(invalid_ids)),
                "unnecessary_refusals": unnecessary_refusals,
                "unnecessary_refusal_denominator": len(valid_ids),
                "unnecessary_refusal_rate": _rate(unnecessary_refusals, len(valid_ids)),
                "valid_use_coverage": _rate(
                    len(valid_ids) - unnecessary_refusals, len(valid_ids)
                ),
                "decision_interpretation_errors": decision_errors,
                "decision_interpretation_denominator": len(eligible_decisions),
                "ranking_interpretation_errors": ranking_errors,
                "ranking_interpretation_denominator": len(eligible_rankings),
                "ranking_changes_vs_naive": sum(
                    records[case_id]["ranking"]
                    != by_policy["naive_aggregation"][case_id]["ranking"]
                    for case_id in ranking_ids
                ),
                "ranking_change_denominator": len(ranking_ids),
                "decision_changes_vs_naive": sum(
                    records[case_id]["decision"]
                    != by_policy["naive_aggregation"][case_id]["decision"]
                    for case_id in decision_ids
                ),
                "decision_change_denominator": len(decision_ids),
                "mean_rule_checks": _rate(
                    sum(records[case_id]["rule_checks"] for case_id in ids), len(ids)
                ),
                "mean_public_metadata_bytes": _rate(
                    sum(records[case_id]["public_metadata_bytes"] for case_id in ids),
                    len(ids),
                ),
                "model_calls": sum(records[case_id]["model_calls"] for case_id in ids),
                "manual_reviews": 0,
            }

        differences: dict[str, Any] = {}
        baseline = by_policy["metadata_only"]
        for policy in by_policy:
            if policy == "metadata_only":
                continue
            invalid_diffs = [
                float(by_policy[policy][case_id]["permission"])
                - float(baseline[case_id]["permission"])
                for case_id in invalid_ids
            ]
            valid_diffs = [
                float(not by_policy[policy][case_id]["permission"])
                - float(not baseline[case_id]["permission"])
                for case_id in valid_ids
            ]
            key = zlib.crc32(f"{family}:{policy}".encode())
            differences[policy] = {
                "false_permission_rate_difference_vs_metadata_only": _bootstrap_difference(
                    invalid_diffs, [0.0] * len(invalid_diffs), BOOTSTRAP_SEED + key
                ),
                "unnecessary_refusal_rate_difference_vs_metadata_only": _bootstrap_difference(
                    valid_diffs, [0.0] * len(valid_diffs), BOOTSTRAP_SEED + key + 1
                ),
            }
        family_summary["paired_bootstrap_differences_vs_metadata_only"] = differences
        family_summary["ranking_estimand_cases"] = len(ranking_ids)
        family_summary["declared_decision_cases"] = len(decision_ids)
        summaries[family] = family_summary
    return summaries


def run() -> dict[str, Any]:
    public_cases = _read_jsonl(PUBLIC_PATH)
    # Freeze every candidate output before evaluator labels are read.
    outputs = candidate_outputs(public_cases)
    evaluator = _read_jsonl(EVALUATOR_PATH)
    if [row["case_id"] for row in public_cases] != [
        row["case_id"] for row in evaluator
    ]:
        raise ValueError(
            "public cases and evaluator outcomes must have matching ordered IDs"
        )
    summaries = summarize(public_cases, evaluator, outputs)
    per_case = []
    labels = {row["case_id"]: row for row in evaluator}
    for case in public_cases:
        case_id = case["case_id"]
        per_case.append(
            {
                "public_case": case,
                "evaluator_outcome": labels[case_id],
                "policy_outputs": {
                    policy: next(
                        row for row in outputs[policy] if row["case_id"] == case_id
                    )
                    for policy in (*POLICIES, "evaluator_oracle")
                },
            }
        )
    return {
        "evidence_class": "internally authored synthetic challenge; not independent external validation",
        "unit": "36 authored cases; not 36 independent real-world tasks",
        "case_sha256": _sha256(PUBLIC_PATH),
        "evaluator_sha256": _sha256(EVALUATOR_PATH),
        "preregistration_sha256": _sha256(PREREG_PATH),
        "policy_code_sha256": _sha256(Path(__file__)),
        "bootstrap": {"resamples": BOOTSTRAP_RESAMPLES, "seed": BOOTSTRAP_SEED},
        "candidate_metrics": summaries,
        "per_case": per_case,
    }


def main() -> None:
    result = run()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        f"wrote {len(result['per_case'])} scored cases to {RESULT_PATH.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
