"""Tests for the frozen public-only operation-policy challenge."""

from __future__ import annotations

import json
from copy import deepcopy

import pytest

from scripts import operation_policy_challenge as challenge


def _case_map() -> dict[str, dict[str, object]]:
    return {
        case["case_id"]: case for case in challenge._read_jsonl(challenge.PUBLIC_PATH)
    }


def test_candidate_input_schema_rejects_evaluator_truth() -> None:
    case = deepcopy(_case_map()["FP01"])
    case["expected_permission"] = True

    with pytest.raises(ValueError, match="frozen public case schema"):
        challenge.candidate_outputs([case])


def test_evaluator_label_changes_do_not_change_public_policy_outputs() -> None:
    public = challenge._read_jsonl(challenge.PUBLIC_PATH)
    evaluator = challenge._read_jsonl(challenge.EVALUATOR_PATH)
    before = challenge.candidate_outputs(public)
    evaluator[0]["expected_permission"] = not evaluator[0]["expected_permission"]
    after = challenge.candidate_outputs(public)

    assert after == before


def test_operation_specific_rule_checks_calibration_and_conflict() -> None:
    cases = _case_map()

    assert challenge.candidate_permission("operation_specific", cases["FP01"])[0]
    assert challenge.candidate_permission("metadata_only", cases["FP10"])[0]
    assert not challenge.candidate_permission("operation_specific", cases["FP10"])[0]
    assert challenge.candidate_permission("metadata_only", cases["EC09"])[0]
    assert not challenge.candidate_permission("operation_specific", cases["EC09"])[0]


def test_relevance_mapping_and_target_mismatch() -> None:
    cases = _case_map()

    assert challenge.candidate_permission("operation_specific", cases["RL02"])[0]
    assert not challenge.candidate_permission("global_label", cases["RL02"])[0]
    assert not challenge.candidate_permission("operation_specific", cases["RL07"])[0]
    assert challenge.candidate_permission("naive_aggregation", cases["RL07"])[0]


def test_summary_is_deterministic_and_retains_case_records() -> None:
    result = challenge.run()
    saved = json.loads(challenge.RESULT_PATH.read_text())

    assert len(result["per_case"]) == 36
    assert result["candidate_metrics"]["forecast_pool"]["n_cases"] == 12
    assert result["bootstrap"] == {"resamples": 2000, "seed": 4701}
    assert result == saved


def test_report_counts_recompute_from_per_case_records() -> None:
    result = json.loads(challenge.RESULT_PATH.read_text())
    for family, summary in result["candidate_metrics"].items():
        rows = [
            row
            for row in result["per_case"]
            if row["public_case"]["operation"] == family
        ]
        valid = [row for row in rows if row["evaluator_outcome"]["expected_permission"]]
        invalid = [
            row for row in rows if not row["evaluator_outcome"]["expected_permission"]
        ]
        for policy, metrics in summary["policies"].items():
            outputs = {
                row["public_case"]["case_id"]: row["policy_outputs"][policy]
                for row in rows
            }
            assert metrics["false_permissions"] == sum(
                outputs[row["public_case"]["case_id"]]["permission"] for row in invalid
            )
            assert metrics["unnecessary_refusals"] == sum(
                not outputs[row["public_case"]["case_id"]]["permission"]
                for row in valid
            )
            decisions = [
                row
                for row in rows
                if row["evaluator_outcome"]["expected_decision"] is not None
                and outputs[row["public_case"]["case_id"]]["decision"] is not None
            ]
            assert metrics["decision_interpretation_errors"] == sum(
                row["evaluator_outcome"]["expected_decision"]
                != outputs[row["public_case"]["case_id"]]["decision"]
                for row in decisions
            )
            rankings = [
                row
                for row in rows
                if row["evaluator_outcome"]["expected_ranking"] is not None
                and outputs[row["public_case"]["case_id"]]["ranking"] is not None
            ]
            assert metrics["ranking_interpretation_errors"] == sum(
                row["evaluator_outcome"]["expected_ranking"]
                != outputs[row["public_case"]["case_id"]]["ranking"]
                for row in rankings
            )
            ranking_cases = [
                row
                for row in rows
                if row["public_case"].get("context", {}).get("ranking_estimand")
            ]
            assert metrics["ranking_changes_vs_naive"] == sum(
                outputs[row["public_case"]["case_id"]]["ranking"]
                != row["policy_outputs"]["naive_aggregation"]["ranking"]
                for row in ranking_cases
            )
            decision_cases = [
                row
                for row in rows
                if "decision_threshold" in row["public_case"].get("context", {})
            ]
            assert metrics["decision_changes_vs_naive"] == sum(
                outputs[row["public_case"]["case_id"]]["decision"]
                != row["policy_outputs"]["naive_aggregation"]["decision"]
                for row in decision_cases
            )
