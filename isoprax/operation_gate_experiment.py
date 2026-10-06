"""Finite synthetic challenge set for comparing commensurability rules."""

from __future__ import annotations

from typing import Any

RULES = ("naive_aggregation", "global_label", "metadata_only", "operation_specific")


def _case(
    name: str,
    operation: str,
    *,
    same_target: bool,
    valid: bool,
    expected_relationship: str | None = None,
    mixture: bool = False,
    mapping: bool = False,
    metric_compatible: bool = True,
    samples_aligned: bool = True,
    weights_declared: bool = True,
    population_same: bool = True,
    transport_validated: bool = False,
    calibration_evidence: bool = True,
    prediction_time_aligned: bool = True,
    heldout_evaluation: bool = True,
    independent_sources: bool = True,
    dependence_model: bool = False,
    rank_fixture: str | None = None,
) -> dict[str, Any]:
    if expected_relationship is None:
        expected_relationship = "same_target" if same_target else "different_targets"
    return {
        "case": name,
        "operation": operation,
        "same_target": same_target,
        "valid": valid,
        "expected_relationship": expected_relationship,
        "mixture_declared": mixture,
        "decision_mapping_declared": mapping,
        "metric_compatible": metric_compatible,
        "samples_aligned": samples_aligned,
        "weights_declared": weights_declared,
        "population_same": population_same,
        "transport_validated": transport_validated,
        "calibration_evidence": calibration_evidence,
        "prediction_time_aligned": prediction_time_aligned,
        "heldout_evaluation": heldout_evaluation,
        "independent_sources": independent_sources,
        "dependence_model": dependence_model,
        "rank_fixture": rank_fixture,
    }


def challenge_cases() -> list[dict[str, Any]]:
    """Return the predeclared, fixed case table used by the synthetic comparison."""
    return [
        _case("compare_same_target", "compare", same_target=True, valid=True),
        _case(
            "compare_equivalent_definition_cross_family",
            "compare",
            same_target=True,
            valid=True,
        ),
        _case("compare_different_event", "compare", same_target=False, valid=False),
        _case(
            "compare_incompatible_metric_units",
            "compare",
            same_target=True,
            valid=False,
            metric_compatible=False,
        ),
        _case(
            "rank_same_target_aligned",
            "rank",
            same_target=True,
            valid=True,
            rank_fixture="balanced",
        ),
        _case(
            "rank_declared_decision_mapping",
            "rank",
            same_target=False,
            valid=True,
            mapping=True,
            expected_relationship="decision_objective",
            rank_fixture="mapped",
        ),
        _case(
            "rank_different_target_no_mapping",
            "rank",
            same_target=False,
            valid=False,
            rank_fixture="separated",
        ),
        _case(
            "rank_same_target_misaligned_sample",
            "rank",
            same_target=True,
            valid=False,
            samples_aligned=False,
            rank_fixture="separated",
        ),
        _case(
            "pool_same_target_predeclared_weights", "pool", same_target=True, valid=True
        ),
        _case(
            "pool_same_target_weights_missing",
            "pool",
            same_target=True,
            valid=False,
            weights_declared=False,
        ),
        _case(
            "pool_declared_mixture",
            "pool",
            same_target=False,
            valid=True,
            mixture=True,
            expected_relationship="declared_mixture",
        ),
        _case(
            "pool_different_target_no_mixture", "pool", same_target=False, valid=False
        ),
        _case(
            "pool_overlapping_rows_unmodeled",
            "pool",
            same_target=True,
            valid=False,
            samples_aligned=False,
        ),
        _case(
            "transfer_same_population_with_calibration",
            "transfer",
            same_target=True,
            valid=True,
        ),
        _case(
            "transfer_shift_validated",
            "transfer",
            same_target=False,
            valid=True,
            population_same=False,
            transport_validated=True,
            expected_relationship="validated_transport",
        ),
        _case(
            "transfer_shift_unvalidated",
            "transfer",
            same_target=False,
            valid=False,
            population_same=False,
        ),
        _case(
            "transfer_calibration_evidence_missing",
            "transfer",
            same_target=True,
            valid=False,
            calibration_evidence=False,
        ),
        _case("average_same_target_same_time", "average", same_target=True, valid=True),
        _case(
            "average_prediction_time_mismatch",
            "average",
            same_target=True,
            valid=False,
            prediction_time_aligned=False,
        ),
        _case("average_different_horizon", "average", same_target=False, valid=False),
        _case(
            "combine_independent_sources",
            "combine",
            same_target=True,
            valid=True,
            independent_sources=True,
        ),
        _case(
            "combine_shared_source_with_model",
            "combine",
            same_target=True,
            valid=True,
            independent_sources=False,
            dependence_model=True,
            expected_relationship="same_target",
        ),
        _case(
            "combine_shared_source_unmodeled",
            "combine",
            same_target=True,
            valid=False,
            independent_sources=False,
        ),
    ]


def _operation_specific(case: dict[str, Any]) -> bool:
    operation = case["operation"]
    same = case["same_target"]
    if operation == "compare":
        return case["metric_compatible"] and case["samples_aligned"] and same
    if operation == "rank":
        same_target_rank = same and case["samples_aligned"]
        mapped_rank = case["decision_mapping_declared"] and case["metric_compatible"]
        return same_target_rank or mapped_rank
    if operation == "pool":
        target_named = same or case["mixture_declared"]
        return target_named and case["weights_declared"] and case["samples_aligned"]
    if operation == "transfer":
        same_population = same and case["population_same"]
        validated_transport = (
            case["transport_validated"] and not case["population_same"]
        )
        return case["calibration_evidence"] and (same_population or validated_transport)
    if operation == "average":
        return same and case["prediction_time_aligned"] and case["heldout_evaluation"]
    if operation == "combine":
        return same and (case["independent_sources"] or case["dependence_model"])
    raise ValueError(f"unknown operation: {operation}")


def _permits(rule: str, case: dict[str, Any]) -> bool:
    if rule == "naive_aggregation":
        return True
    if rule == "global_label":
        return case["same_target"]
    if rule == "metadata_only":
        operation = case["operation"]
        same = case["same_target"]
        if operation == "compare":
            return same and case["metric_compatible"]
        if operation == "rank":
            return (same and case["metric_compatible"]) or case[
                "decision_mapping_declared"
            ]
        if operation == "pool":
            return (same and case["weights_declared"]) or (
                case["mixture_declared"] and case["weights_declared"]
            )
        if operation == "transfer":
            return (same and case["population_same"]) or case["transport_validated"]
        if operation == "average":
            return same
        if operation == "combine":
            return same
        raise ValueError(f"unknown operation: {operation}")
    if rule == "operation_specific":
        return _operation_specific(case)
    raise ValueError(f"unknown rule: {rule}")


def _relationship(rule: str, case: dict[str, Any]) -> str:
    if rule == "naive_aggregation":
        return "same_target"
    if rule == "global_label":
        return "same_target" if case["same_target"] else "different_targets"
    if case["mixture_declared"] and case["operation"] == "pool":
        return "declared_mixture"
    if case["decision_mapping_declared"] and case["operation"] == "rank":
        return "decision_objective"
    if case["transport_validated"] and case["operation"] == "transfer":
        return "validated_transport"
    return "same_target" if case["same_target"] else "different_targets"


def _ranked_selections(fixture: str) -> tuple[set[str], set[str]]:
    if fixture == "balanced":
        a = [0.95, 0.75, 0.55, 0.35, 0.15, 0.13, 0.11, 0.09, 0.07, 0.05]
        b = [0.90, 0.70, 0.50, 0.30, 0.14, 0.12, 0.10, 0.08, 0.06, 0.04]
    elif fixture == "mapped":
        a = [0.92, 0.82, 0.72, 0.62, 0.15, 0.13, 0.11, 0.09, 0.07, 0.05]
        b = [0.88, 0.78, 0.68, 0.58, 0.14, 0.12, 0.10, 0.08, 0.06, 0.04]
    else:
        a = [0.32, 0.29, 0.26, 0.23, 0.20, 0.17, 0.14, 0.11, 0.08, 0.05]
        b = [0.98, 0.95, 0.92, 0.89, 0.20, 0.17, 0.14, 0.11, 0.08, 0.05]
    rows = [(f"A-{i}", score) for i, score in enumerate(a)] + [
        (f"B-{i}", score) for i, score in enumerate(b)
    ]
    global_top = {row[0] for row in sorted(rows, key=lambda row: (-row[1], row[0]))[:4]}
    local_top = {
        *(
            f"A-{i}"
            for i in sorted(range(10), key=lambda index: (-a[index], index))[:2]
        ),
        *(
            f"B-{i}"
            for i in sorted(range(10), key=lambda index: (-b[index], index))[:2]
        ),
    }
    return global_top, local_top


def _rule_summary(rule: str, cases: list[dict[str, Any]]) -> dict[str, Any]:
    false_permissions = 0
    unnecessary_refusals = 0
    interpretation_errors = 0
    rank_cases = 0
    rank_changed_cases = 0
    decision_changed_records = 0
    valid_cases = sum(case["valid"] for case in cases)
    invalid_cases = len(cases) - valid_cases
    for case in cases:
        permitted = _permits(rule, case)
        if permitted and not case["valid"]:
            false_permissions += 1
        if not permitted and case["valid"]:
            unnecessary_refusals += 1
        if _relationship(rule, case) != case["expected_relationship"]:
            interpretation_errors += 1
        fixture = case["rank_fixture"]
        if fixture is not None:
            rank_cases += 1
            global_top, local_top = _ranked_selections(fixture)
            expected = global_top if case["valid"] else local_top
            actual = global_top if permitted else local_top
            difference = len(expected.symmetric_difference(actual))
            if difference:
                rank_changed_cases += 1
                decision_changed_records += difference
    return {
        "case_count": len(cases),
        "false_permissions": false_permissions,
        "invalid_case_denominator": invalid_cases,
        "false_permission_rate": false_permissions / invalid_cases
        if invalid_cases
        else 0.0,
        "unnecessary_refusals": unnecessary_refusals,
        "valid_case_denominator": valid_cases,
        "unnecessary_refusal_rate": unnecessary_refusals / valid_cases
        if valid_cases
        else 0.0,
        "interpretation_errors": interpretation_errors,
        "interpretation_error_rate": interpretation_errors / len(cases)
        if cases
        else 0.0,
        "ranking_cases": rank_cases,
        "ranking_changed_cases": rank_changed_cases,
        "decision_changed_records": decision_changed_records,
        "decision_rule": (
            "review top 20% globally if ranking is permitted; otherwise review top 20% "
            "within each target; compare selected IDs with the case's declared valid action"
        ),
    }


def run_gate_experiment() -> dict[str, Any]:
    cases = challenge_cases()
    summary = {rule: _rule_summary(rule, cases) for rule in RULES}
    return {
        "status": "executed synthetic rule challenge set",
        "case_count": len(cases),
        "rules": {
            "naive_aggregation": "always permits the requested operation and labels outputs same-target",
            "global_label": "permits every operation only when the outcome target matches",
            "metadata_only": "uses target equality, declared mixture/mapping, population, weights, and dependency metadata",
            "operation_specific": "checks target, operation-specific data, validation, timing, sample, mapping, and dependence conditions",
        },
        "summary": summary,
        "cases": [
            {
                "case": case["case"],
                "operation": case["operation"],
                "expected_permission": case["valid"],
                "expected_target_relationship": case["expected_relationship"],
                "permissions": {rule: _permits(rule, case) for rule in RULES},
                "interpretations": {rule: _relationship(rule, case) for rule in RULES},
            }
            for case in cases
        ],
        "claim_boundary": (
            "Fixed synthetic challenge set authored from the candidate operation conditions. "
            "Counts are not independent adjudication or field error rates."
        ),
    }
