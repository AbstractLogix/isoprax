"""Deterministic synthetic experiments for the public IsoPrax research program.

These fixtures are structural research evidence. They do not measure deployed
predictive performance or establish a conformance tier.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from sklearn.metrics import roc_auc_score

from .commensurability import (
    ObservationProcess,
    OutcomeDefinition,
    Threshold,
    Window,
    check_commensurable,
)
from .evaluation import brier_score, expected_calibration_error
from .events import ChangeEvent, RunEvent
from .jepa import (
    JEPAAnomalyStrategy,
    JEPABackendConfig,
    JEPARiskStrategy,
    JEPATrainingPair,
    JEPAWorldModel,
)
from .operation_gate_experiment import run_gate_experiment
from .strategies import Calibrator

SEED = 4605
BOOTSTRAP_RESAMPLES = 500
BOOTSTRAP_SEED = 46051
BOOTSTRAP_METHOD = "two-sided 95% percentile bootstrap"


def _definition(
    identifier: str, event: str, process: str, hours: float, threshold: str
) -> OutcomeDefinition:
    return OutcomeDefinition(
        id=identifier,
        event=event,
        observation_process=ObservationProcess(kind=process),
        window=Window(duration=hours, unit="hours", anchor="after forecast time"),
        thresholds=(Threshold(metric=threshold, operator=">=", value=1),),
        description="Synthetic experiment target; not a real-world label.",
    )


def _metric_values(scores: Sequence[float], outcomes: Sequence[int]) -> dict[str, Any]:
    n = len(outcomes)
    positives = int(sum(outcomes))
    auc = None
    auc_reason = "both outcome classes are required"
    if positives not in (0, n) and len(set(scores)) > 1:
        auc = float(roc_auc_score(outcomes, scores))
        auc_reason = None
    elif len(set(scores)) < 2:
        auc_reason = "constant forecast scores do not discriminate"
    return {
        "n": n,
        "positive_count": positives,
        "negative_count": n - positives,
        "event_rate": positives / n if n else None,
        "mean_forecast": float(np.mean(scores)) if n else None,
        "ece_10_equal_width_bins": expected_calibration_error(scores, outcomes, 10),
        "brier_score": brier_score(scores, outcomes),
        "roc_auc": auc,
        "roc_auc_unavailable_reason": auc_reason,
    }


def _bootstrap_metrics(
    scores: Sequence[float], outcomes: Sequence[int], seed: int
) -> dict[str, Any]:
    values = np.asarray(scores, dtype=float)
    labels = np.asarray(outcomes, dtype=int)
    rng = np.random.default_rng(seed)
    draws: dict[str, list[float]] = {
        "event_rate": [],
        "ece": [],
        "brier": [],
        "auc": [],
    }
    for _ in range(BOOTSTRAP_RESAMPLES):
        indexes = rng.integers(0, len(labels), size=len(labels))
        sampled_scores = values[indexes]
        sampled_labels = labels[indexes]
        draws["event_rate"].append(float(np.mean(sampled_labels)))
        draws["ece"].append(
            expected_calibration_error(
                sampled_scores.tolist(), sampled_labels.tolist(), 10
            )
        )
        draws["brier"].append(
            brier_score(sampled_scores.tolist(), sampled_labels.tolist())
        )
        if (
            len(set(sampled_labels.tolist())) == 2
            and len(set(sampled_scores.tolist())) > 1
        ):
            draws["auc"].append(float(roc_auc_score(sampled_labels, sampled_scores)))

    def interval(items: list[float]) -> list[float] | None:
        if not items:
            return None
        low, high = np.percentile(items, [2.5, 97.5])
        return [float(low), float(high)]

    return {
        "method": BOOTSTRAP_METHOD,
        "resamples": BOOTSTRAP_RESAMPLES,
        "seed": seed,
        "event_rate_interval": interval(draws["event_rate"]),
        "ece_interval": interval(draws["ece"]),
        "brier_interval": interval(draws["brier"]),
        "roc_auc_interval": interval(draws["auc"]),
        "roc_auc_usable_resamples": len(draws["auc"]),
        "scope": "sampling variation conditional on this synthetic generator",
    }


def _top_fraction(scores: Sequence[float], outcomes: Sequence[int]) -> dict[str, Any]:
    n = len(scores)
    k = max(1, math.ceil(n * 0.20))
    selected = sorted(range(n), key=lambda index: (-scores[index], index))[:k]
    positives = sum(outcomes[index] for index in selected)
    return {
        "fraction": 0.20,
        "selected_count": k,
        "positive_count": positives,
        "selected_event_rate": positives / k,
        "positive_capture_rate": positives / sum(outcomes) if sum(outcomes) else None,
        "rank_order": "forecast descending; stable row order breaks ties",
    }


def _lane(name: str, definition: dict[str, str]) -> dict[str, Any]:
    scores = [0.80] * 100
    outcomes = [1] * 80 + [0] * 20
    metrics = _metric_values(scores, outcomes)
    return {
        "lane": name,
        "outcome_definition": definition,
        "n": len(outcomes),
        "forecast": 0.80,
        "metrics": metrics,
        "permitted_operations": [
            "report this lane's calibration against its own declared target",
            "include its risk in a separately named, predeclared mixture estimand",
        ],
        "prohibited_interpretations": [
            "0.80 is the probability of the other lane's event",
            "the two event definitions describe one common failure event",
        ],
    }


def run_benchmark_a() -> dict[str, Any]:
    change_target = {
        "id": "synthetic.change.fix-linked-defect.30d",
        "event": "change is linked to a defect fix",
        "observation_process": "repository issue and fix-link observation",
        "window": "30 days after change",
        "threshold": "at least one qualifying fix link",
    }
    operations_target = {
        "id": "synthetic.operations.threshold-breach.30m",
        "event": "service telemetry crosses a failure threshold",
        "observation_process": "deployment telemetry threshold observation",
        "window": "30 minutes after deployment",
        "threshold": "declared service-level threshold",
    }
    lanes = [_lane("change", change_target), _lane("operational", operations_target)]
    all_scores = [0.80] * 200
    all_outcomes = [1] * 160 + [0] * 40
    weights = {"change": 0.5, "operational": 0.5}
    mixture = {
        "target_definition": {
            "id": "synthetic.mixture.change-30d-and-operational-30m.equal-weight",
            "kind": "equal-weight mixture of lane-specific event risks",
            "component_targets": {
                "change": change_target["id"],
                "operational": operations_target["id"],
            },
            "sampling_rule": (
                "select one lane with its declared weight, then observe that lane's own event"
            ),
        },
        "estimand": (
            "equal-weight mean of the 30-day change-label event risk and the "
            "30-minute operational-threshold event risk; select a lane with "
            "probability 0.5, then observe that lane's own event"
        ),
        "weights": weights,
        "is_one_common_event": False,
        "metrics": _metric_values(all_scores, all_outcomes),
    }

    control_definition = {
        "id": "synthetic.shared.threshold-breach.30m",
        "event": "service telemetry crosses the declared failure threshold",
        "observation_process": "same deployment telemetry threshold observation",
        "window": "30 minutes after deployment",
        "threshold": "same declared service-level threshold",
    }
    control_lanes = [
        _lane("control-a", control_definition),
        _lane("control-b", control_definition),
    ]
    control = {
        "target": control_definition,
        "weights": {"control-a": 0.5, "control-b": 0.5},
        "estimand": "same declared event risk in a 50:50 mixture of two synthetic cohorts",
        "metrics": _metric_values(all_scores, all_outcomes),
        "permitted_operations": [
            "pool target-local calibration diagnostics for the declared 50:50 cohort mixture",
            "compare forecasts against the same event definition and observation process",
        ],
    }
    return {
        "status": "executed synthetic benchmark",
        "lanes": lanes,
        "permitted_operations": [
            "report calibration against each lane's own target",
            "report a numeric result for the exact declared 50:50 lane-risk mixture",
            "pool metrics in the valid same-target control",
        ],
        "prohibited_or_unsupported_interpretations": [
            "equal probabilities imply one common event",
            "the different-target 0.80 mixture is a common-event probability",
            "calibration of each lane establishes cross-target equivalence",
        ],
        "invalid_interpretation": (
            "the pooled 0.80 is the probability of one common event across both lanes"
        ),
        "declared_numeric_mixture": mixture,
        "valid_same_target_control": {"lanes": control_lanes, **control},
    }


def _change(index: int, cohort: str) -> ChangeEvent:
    return ChangeEvent(
        id=f"{cohort}-change-{index:04d}",
        timestamp="2025-01-01T00:00:00+00:00",
        source="synthetic-jepa-experiment",
        repo=f"repo-{index % 7}",
        change_ref=f"{cohort}-ref-{index:04d}",
        author=f"author-{index % 5}",
        files_touched=[f"service/{index % 11}.py"],
        loc_added=(index * 17) % 241,
        loc_removed=(index * 7) % 83,
        features={"synthetic_complexity": (index % 23) / 22.0},
    )


def _state(index: int, cohort: str) -> tuple[tuple[float, ...], ...]:
    phase = index * 0.173 + (0.31 if cohort.endswith("b") else 0.0)
    return tuple(
        (
            math.sin(phase + step * 0.21),
            math.cos(phase * 0.73 - step * 0.19),
            ((index + step * 3) % 29) / 28.0,
        )
        for step in range(4)
    )


def _context(index: int, cohort: str) -> dict[str, Any]:
    change = _change(index, cohort)
    pre_state = _state(index, cohort)
    delta = ((index % 13) + 1) * 0.035
    post_state = tuple(tuple(value + delta for value in row) for row in pre_state)
    return {"change": change, "pre_state": pre_state, "post_state": post_state}


def _fit_shared_model() -> JEPAWorldModel:
    pairs = []
    for index in range(24):
        context = _context(index, "training")
        delta = 0.04 + (index % 7) * 0.025
        post_state = tuple(
            tuple(value + delta for value in row) for row in context["pre_state"]
        )
        pairs.append(
            JEPATrainingPair(context["change"], context["pre_state"], post_state)
        )
    model = JEPAWorldModel(
        JEPABackendConfig(
            change_embedding_dim=12,
            state_embedding_dim=5,
            ridge_lambda=0.01,
            hash_seed="isoprax-experiment-046-v1",
        )
    )
    model.fit(pairs)
    return model


def _probabilities(raw: Sequence[float], intercept: float, slope: float) -> np.ndarray:
    values = np.asarray(raw, dtype=float)
    standard_deviation = float(np.std(values)) or 1.0
    z = (values - float(np.mean(values))) / standard_deviation
    logits = np.clip(intercept + slope * z, -8.0, 8.0)
    return 1.0 / (1.0 + np.exp(-logits))


def _labels(probabilities: Sequence[float], seed: int) -> list[int]:
    rng = np.random.default_rng(seed)
    return (
        (rng.random(len(probabilities)) < np.asarray(probabilities))
        .astype(int)
        .tolist()
    )


def _record_target(
    target_id: str,
    cohort: str,
    definition: OutcomeDefinition,
    scores: list[float],
    outcomes: list[int],
    calibration_n: int,
    model_identity: str,
    seed: int,
) -> dict[str, Any]:
    base = _metric_values(scores, outcomes)
    return {
        "target_id": target_id,
        "cohort": cohort,
        "family": "change" if target_id.startswith("change.") else "operational",
        "calibration_method": "isotonic; fitted separately for this target",
        "outcome_definition": {
            "id": definition.id,
            "event": definition.event,
            "observation_process": {
                "kind": definition.observation_process.kind,
                "parameters": dict(definition.observation_process.parameters),
            },
            "window": {
                "duration": definition.window.duration,
                "unit": definition.window.unit,
                "anchor": definition.window.anchor,
            },
            "thresholds": [
                {
                    "metric": threshold.metric,
                    "operator": threshold.operator,
                    "value": threshold.value,
                }
                for threshold in definition.thresholds
            ],
        },
        "backend_identity": model_identity,
        "sample_counts": {
            "calibration": calibration_n,
            "test": base["n"],
            "positive_test": base["positive_count"],
            "negative_test": base["negative_count"],
        },
        "metrics": base,
        "uncertainty": _bootstrap_metrics(scores, outcomes, seed),
        "ranking": _top_fraction(scores, outcomes),
    }


def _semantic_comparison(
    left: OutcomeDefinition, right: OutcomeDefinition
) -> dict[str, Any]:
    result = check_commensurable(left, right)
    return {
        "left_target": result.left_id,
        "right_target": result.right_id,
        "level": result.level,
        "pooling_allowed": result.pooling_allowed,
        "differing_fields": result.differing_fields,
    }


def _risk_target(
    model: JEPAWorldModel,
    definition: OutcomeDefinition,
    target_id: str,
    cohort: str,
    seed: int,
) -> tuple[dict[str, Any], list[float], list[int]]:
    calibration_events = [_change(i, f"{cohort}-cal") for i in range(240)]
    test_events = [_change(i + 1000, f"{cohort}-test") for i in range(300)]
    calibration_raw = [model.raw_change_risk(event) for event in calibration_events]
    test_raw = [model.raw_change_risk(event) for event in test_events]
    calibration_prob = _probabilities(calibration_raw, -0.25, 0.85)
    test_prob = _probabilities(test_raw, -0.25, 0.85)
    calibration_y = _labels(calibration_prob, seed)
    test_y = _labels(test_prob, seed + 1)
    strategy = JEPARiskStrategy(
        model, calibrator=Calibrator(), outcome_definition=definition
    )
    strategy.fit_calibrator(calibration_events, calibration_y)
    forecasts = [strategy.score(event, {}).score for event in test_events]
    record = _record_target(
        target_id,
        cohort,
        definition,
        forecasts,
        test_y,
        len(calibration_y),
        model.backend_identity,
        seed + 2,
    )
    return record, forecasts, test_y


def _anomaly_target(
    model: JEPAWorldModel,
    definition: OutcomeDefinition,
    target_id: str,
    cohort: str,
    seed: int,
    intercept: float = -0.25,
    slope: float = 0.85,
) -> tuple[dict[str, Any], list[float], list[int]]:
    calibration_cases = [
        (
            RunEvent(
                id=f"{cohort}-cal-run-{i}",
                timestamp="2025-01-01T00:00:00+00:00",
                source="synthetic",
                job_type="service",
                job_identifier=f"cal-{i}",
                exit_status="complete",
            ),
            _context(i, f"{cohort}-cal"),
        )
        for i in range(240)
    ]
    test_cases = [
        (
            RunEvent(
                id=f"{cohort}-test-run-{i}",
                timestamp="2025-01-02T00:00:00+00:00",
                source="synthetic",
                job_type="service",
                job_identifier=f"test-{i}",
                exit_status="complete",
            ),
            _context(i + 1000, f"{cohort}-test"),
        )
        for i in range(300)
    ]
    calibration_raw = [
        model.raw_anomaly_score(
            case[1]["change"], case[1]["pre_state"], case[1]["post_state"]
        )
        for case in calibration_cases
    ]
    test_raw = [
        model.raw_anomaly_score(
            case[1]["change"], case[1]["pre_state"], case[1]["post_state"]
        )
        for case in test_cases
    ]
    calibration_y = _labels(_probabilities(calibration_raw, intercept, slope), seed)
    test_y = _labels(_probabilities(test_raw, intercept, slope), seed + 1)
    strategy = JEPAAnomalyStrategy(
        model, calibrator=Calibrator(), outcome_definition=definition
    )
    strategy.fit_calibrator(calibration_cases, calibration_y)
    forecasts = [strategy.evaluate(run, context).score for run, context in test_cases]
    record = _record_target(
        target_id,
        cohort,
        definition,
        forecasts,
        test_y,
        len(calibration_y),
        model.backend_identity,
        seed + 2,
    )
    return record, forecasts, test_y


def _pool_same_target(
    records: list[tuple[str, list[float], list[int]]],
    target_definition: OutcomeDefinition,
) -> dict[str, Any]:
    weights = {cohort: 1 / len(records) for cohort, _, _ in records}
    scores = [score for _, cohort_scores, _ in records for score in cohort_scores]
    outcomes = [
        outcome for _, _, cohort_outcomes in records for outcome in cohort_outcomes
    ]
    ranked_rows = [
        (cohort, index, score)
        for cohort, cohort_scores, _ in records
        for index, score in enumerate(cohort_scores)
    ]
    selected_count = max(1, math.ceil(len(ranked_rows) * 0.20))
    selected = sorted(ranked_rows, key=lambda row: (-row[2], row[0], row[1]))[
        :selected_count
    ]
    ranking_by_cohort = {
        cohort: sum(row[0] == cohort for row in selected) for cohort, _, _ in records
    }
    return {
        "estimand": (
            "forecast error and calibration for the same operational threshold event "
            "in an equally weighted mixture of two synthetic cohorts"
        ),
        "target_definition_id": target_definition.id,
        "weights": weights,
        "metrics": _metric_values(scores, outcomes),
        "uncertainty": _bootstrap_metrics(scores, outcomes, BOOTSTRAP_SEED + 9),
        "ranking": _top_fraction(scores, outcomes),
        "ranking_selected_count_by_cohort": ranking_by_cohort,
    }


def _cross_target_ranking_diagnostic(
    records: list[tuple[str, list[float], list[int]]],
) -> dict[str, Any]:
    combined = [
        (cohort, index, score)
        for cohort, scores, _ in records
        for index, score in enumerate(scores)
    ]
    k = max(1, math.ceil(len(combined) * 0.20))
    global_selected = sorted(combined, key=lambda row: (-row[2], row[0], row[1]))[:k]
    selected_by_target = {
        cohort: sum(row[0] == cohort for row in global_selected)
        for cohort, _, _ in records
    }
    local_selected = {
        cohort: set(
            sorted(range(len(scores)), key=lambda index: (-scores[index], index))[
                : max(1, math.ceil(len(scores) * 0.20))
            ]
        )
        for cohort, scores, _ in records
    }
    overlap = {
        cohort: sum(
            row[0] == cohort and row[1] in local_selected[cohort]
            for row in global_selected
        )
        for cohort, _, _ in records
    }
    return {
        "interpretation_permitted": False,
        "meaning": "diagnostic only; raw cross-target ranks have no shared risk meaning",
        "global_top_20_selected_count_by_target": selected_by_target,
        "overlap_with_each_target_local_top_20": overlap,
    }


def run_shared_model_experiment() -> dict[str, Any]:
    model = _fit_shared_model()
    operational_1h = _definition(
        "synthetic.operational.failure.1h",
        "operational run crosses its failure threshold",
        "synthetic replay telemetry threshold process",
        1,
        "threshold-1",
    )
    operational_24h = _definition(
        "synthetic.operational.failure.24h",
        "operational run crosses its failure threshold",
        "synthetic replay telemetry threshold process",
        24,
        "threshold-1",
    )
    change_30d = _definition(
        "synthetic.change.fix-linked-defect.30d",
        "change is linked to a defect fix",
        "synthetic repository fix-link process",
        30 * 24,
        "at-least-one-fix-link",
    )
    family_result, family_scores, family_y = _risk_target(
        model, change_30d, "change.defect.30d", "different-family", SEED + 10
    )
    short_result, short_scores, short_y = _anomaly_target(
        model,
        operational_1h,
        "operational.failure.1h",
        "horizon-pair",
        SEED + 20,
        intercept=-0.45,
        slope=0.75,
    )
    long_result, long_scores, long_y = _anomaly_target(
        model,
        operational_24h,
        "operational.failure.24h",
        "horizon-pair",
        SEED + 20,
        intercept=0.20,
        slope=0.75,
    )

    cohort_a, scores_a, outcomes_a = _anomaly_target(
        model, operational_1h, operational_1h.id, "control-a", SEED + 40
    )
    cohort_b, scores_b, outcomes_b = _anomaly_target(
        model, operational_1h, operational_1h.id, "control-b", SEED + 50
    )
    controls = [cohort_a, cohort_b]
    mixture = _pool_same_target(
        [("control-a", scores_a, outcomes_a), ("control-b", scores_b, outcomes_b)],
        operational_1h,
    )
    unpooled = [family_result, short_result, long_result]
    return {
        "status": "executed synthetic shared-model experiment",
        "backend_identity": model.backend_identity,
        "state_representation_identity": model.state_representation_identity,
        "question": "Does one shared model identity justify cross-target comparison or pooling?",
        "outcome_definition_comparisons": {
            "different_family": _semantic_comparison(change_30d, operational_1h),
            "different_horizon": _semantic_comparison(operational_1h, operational_24h),
            "same_target_control": _semantic_comparison(operational_1h, operational_1h),
        },
        "cases": {
            "different_family": {
                "targets": [family_result, short_result],
                "pooled_metrics": None,
                "pooling_reason": "Change defect-link and Operational threshold outcomes differ.",
                "naive_cross_target_ranking_diagnostic": _cross_target_ranking_diagnostic(
                    [
                        ("change", family_scores, family_y),
                        ("operational", short_scores, short_y),
                    ]
                ),
            },
            "different_horizon": {
                "targets": [short_result, long_result],
                "pooled_metrics": None,
                "pooling_reason": "The 1-hour and 24-hour event windows define different targets.",
                "paired_test_rows": len(short_y),
                "short_events_also_positive_at_24_hours": sum(
                    short <= long for short, long in zip(short_y, long_y)
                ),
                "short_events_are_subset_of_24_hour_events": all(
                    short <= long for short, long in zip(short_y, long_y)
                ),
                "naive_cross_target_ranking_diagnostic": _cross_target_ranking_diagnostic(
                    [("1h", short_scores, short_y), ("24h", long_scores, long_y)]
                ),
            },
            "same_target_positive_control": {
                "targets": controls,
                "declared_estimand": mixture["estimand"],
                "weights": mixture["weights"],
                "pooled_metrics": mixture,
            },
        },
        "target_results": unpooled,
        "claim_boundary": (
            "Synthetic, deterministic reference experiment. Shared identity is observed, "
            "but does not establish equal outcome semantics, real-world efficacy, or "
            "Semantic/Full Conformance."
        ),
    }


def run_all_experiments() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "synthetic": True,
        "seed": SEED,
        "bootstrap": {
            "method": BOOTSTRAP_METHOD,
            "resamples": BOOTSTRAP_RESAMPLES,
            "target_specific_seed_recorded_per_metric": True,
        },
        "benchmark_a": run_benchmark_a(),
        "shared_model": run_shared_model_experiment(),
        "gate_comparison": run_gate_experiment(),
        "claim_boundary": (
            "All newly generated results are synthetic research evidence only. They do not "
            "establish predictive efficacy, Semantic/Full Conformance, or production validity."
        ),
    }


def canonical_json(result: dict[str, Any]) -> str:
    return json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="write canonical JSON to this path")
    args = parser.parse_args(argv)
    rendered = canonical_json(run_all_experiments()) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
