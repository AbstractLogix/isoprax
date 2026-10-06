from __future__ import annotations

import json

import pytest

from isoprax.operation_gate_experiment import (
    _operation_specific,
    _permits,
    run_gate_experiment,
)
from isoprax.research_experiments import (
    _bootstrap_metrics,
    _metric_values,
    canonical_json,
    main,
    run_benchmark_a,
    run_shared_model_experiment,
)


def test_benchmark_a_reports_different_targets_and_valid_control() -> None:
    result = run_benchmark_a()
    lanes = result["lanes"]

    assert [lane["metrics"]["n"] for lane in lanes] == [100, 100]
    for lane in lanes:
        assert abs(lane["metrics"]["mean_forecast"] - 0.8) < 1e-12
        assert lane["metrics"]["event_rate"] == 0.8
        assert abs(lane["metrics"]["brier_score"] - 0.16) < 1e-12
    assert lanes[0]["outcome_definition"] != lanes[1]["outcome_definition"]

    mixture = result["declared_numeric_mixture"]
    assert mixture["target_definition"]["id"] == (
        "synthetic.mixture.change-30d-and-operational-30m.equal-weight"
    )
    assert mixture["weights"] == {"change": 0.5, "operational": 0.5}
    assert mixture["is_one_common_event"] is False
    assert mixture["metrics"]["mean_forecast"] == 0.8
    assert result["valid_same_target_control"]["metrics"]["event_rate"] == 0.8
    assert any(
        "one common event" in text
        for text in result["prohibited_or_unsupported_interpretations"]
    )


def test_shared_model_keeps_targets_separate_and_names_only_valid_pool() -> None:
    result = run_shared_model_experiment()
    cases = result["cases"]

    assert result["backend_identity"]
    for target in result["target_results"]:
        assert target["backend_identity"] == result["backend_identity"]
        assert target["sample_counts"]["calibration"] == 240
        assert target["sample_counts"]["test"] == 300
        assert (
            target["metrics"]["positive_count"] + target["metrics"]["negative_count"]
            == 300
        )
        assert target["uncertainty"]["method"] == "two-sided 95% percentile bootstrap"
        assert target["ranking"]["selected_count"] == 60

    assert cases["different_family"]["pooled_metrics"] is None
    assert cases["different_horizon"]["pooled_metrics"] is None
    comparisons = result["outcome_definition_comparisons"]
    assert comparisons["different_family"]["level"] == "irreducible"
    assert comparisons["different_horizon"]["level"] == "bridgeable"
    assert comparisons["different_horizon"]["pooling_allowed"] is False
    assert comparisons["same_target_control"]["level"] == "direct"
    assert (
        cases["different_horizon"]["targets"][0]["metrics"]["event_rate"]
        < cases["different_horizon"]["targets"][1]["metrics"]["event_rate"]
    )
    assert cases["different_horizon"]["paired_test_rows"] == 300
    assert (
        cases["different_horizon"]["short_events_are_subset_of_24_hour_events"] is True
    )
    assert cases["same_target_positive_control"]["weights"] == {
        "control-a": 0.5,
        "control-b": 0.5,
    }
    assert (
        cases["same_target_positive_control"]["pooled_metrics"]["metrics"]["n"] == 600
    )


def test_operation_gate_comparison_reports_all_rules_and_error_measures() -> None:
    result = run_gate_experiment()
    summary = result["summary"]

    assert result["case_count"] == 23
    assert set(summary) == {
        "naive_aggregation",
        "global_label",
        "metadata_only",
        "operation_specific",
    }
    required = {
        "false_permissions",
        "unnecessary_refusals",
        "interpretation_errors",
        "ranking_changed_cases",
        "decision_changed_records",
    }
    assert all(required <= set(values) for values in summary.values())
    assert summary["operation_specific"]["false_permissions"] == 0
    assert summary["operation_specific"]["unnecessary_refusals"] == 0
    assert summary["metadata_only"]["false_permissions"] > 0
    assert (
        summary["naive_aggregation"]["false_permissions"]
        > summary["metadata_only"]["false_permissions"]
    )


def test_benchmark_json_is_canonical_and_reproducible() -> None:
    first = canonical_json(run_benchmark_a())
    second = canonical_json(run_benchmark_a())
    assert first == second


def test_metrics_mark_auc_unavailable_for_constant_or_single_class_data() -> None:
    constant_scores = _metric_values([0.5, 0.5], [0, 1])
    single_class = _metric_values([0.2, 0.8], [1, 1])

    assert constant_scores["roc_auc"] is None
    assert "constant forecast" in constant_scores["roc_auc_unavailable_reason"]
    assert single_class["roc_auc"] is None
    assert "both outcome classes" in single_class["roc_auc_unavailable_reason"]
    interval = _bootstrap_metrics([0.2, 0.8], [1, 1], seed=7)
    assert interval["roc_auc_interval"] is None
    assert interval["roc_auc_usable_resamples"] == 0


def test_runner_cli_writes_canonical_json_and_stdout(tmp_path, capsys) -> None:
    output_path = tmp_path / "nested" / "results.json"
    assert main(["--output", str(output_path)]) == 0
    written = output_path.read_text(encoding="utf-8")
    assert written.endswith("\n")
    json.loads(written)

    assert main([]) == 0
    assert json.loads(capsys.readouterr().out)


def test_gate_rejects_unknown_operation_and_rule() -> None:
    with pytest.raises(ValueError, match="unknown operation"):
        _operation_specific({"operation": "invented", "same_target": False})
    with pytest.raises(ValueError, match="unknown operation"):
        _permits(
            "metadata_only",
            {"operation": "invented", "same_target": False},
        )
    with pytest.raises(ValueError, match="unknown rule"):
        _permits("invented", {})
