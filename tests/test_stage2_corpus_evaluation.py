import json
from dataclasses import replace

import pytest

from isoprax.admission import CorpusRow
from isoprax.commensurability import OutcomeDefinition
from isoprax.stage2_corpus_evaluation import (
    CLAIM_BOUNDARY,
    CorpusEvaluationGate,
    CorpusEvaluationProfile,
    CorpusEvaluationReport,
    evaluate_stage2_corpus,
    validate_stage2_corpus_evaluation_report,
)


def definition(identifier: str, event: str = "latency threshold crossed"):
    return OutcomeDefinition(
        identifier,
        event,
        {"kind": "shared-http", "parameters": {"endpoint": "/bench"}},
        {"duration": 10, "unit": "minute", "anchor": "score_time"},
        ({"metric": "p99", "operator": ">", "value": 0.5},),
    )


def profile(**changes):
    base = CorpusEvaluationProfile(
        "public-system",
        "feasibility-report-id",
        "predeclared-artifact-hash",
        "corpus-artifact-hash",
        definition("change-definition"),
        definition("operational-definition"),
        "change_score",
        "operational_score",
        "PT10M",
        "threshold-v1",
        "public-replay",
        ("corpus.json", "report.json"),
        8,
        4,
        4,
        0.05,
    )
    return replace(base, **changes)


def rows(scores=(0.25, 0.25, 0.25, 0.25, 0.75, 0.75, 0.75, 0.75), outcomes=None):
    outcomes = outcomes or (
        "observed_positive",
        "observed_negative",
        "observed_negative",
        "observed_negative",
        "observed_positive",
        "observed_positive",
        "observed_positive",
        "observed_negative",
    )
    return tuple(
        CorpusRow(
            f"row-{index}",
            "public-system",
            f"change-{index}",
            f"deployment-{index}",
            f"observation-{index}",
            "test",
            f"2026-01-0{index + 1}T00:00:00+00:00",
            outcome,
            {"change_score": score, "operational_score": score},
            ("shared-observation",),
            True,
            "PT10M",
            "threshold-v1",
            prediction_field_observed_at={
                "change_score": "2025-12-31T00:00:00+00:00",
                "operational_score": "2025-12-31T00:00:00+00:00",
            },
        )
        for index, (score, outcome) in enumerate(zip(scores, outcomes))
    )


def test_balanced_shared_corpus_qualifies_per_family_without_pooling():
    report = evaluate_stage2_corpus(rows(), profile())

    assert report.status == "qualified"
    assert report.counts["test_labeled"] == 8
    assert report.family_reports["change"]["metrics"]["auc"] == 0.75
    assert report.family_reports["operational"]["metrics"]["auc"] == 0.75
    assert report.pooling["status"] == "withheld"
    validate_stage2_corpus_evaluation_report(report)


def test_constant_score_predictor_is_inconclusive_despite_calibration():
    report = evaluate_stage2_corpus(rows(scores=(0.5,) * 8), profile())

    assert report.status == "inconclusive"
    assert report.family_reports["change"]["metrics"]["score_variance"] == 0.0
    assert "degenerate" in report.family_reports["change"]["reason"]


def test_missing_outcome_class_is_inconclusive():
    report = evaluate_stage2_corpus(
        rows(outcomes=("observed_positive",) * 8), profile()
    )

    assert report.status == "inconclusive"
    assert report.counts["negative"] == 0
    assert "outcome class" in report.family_reports["change"]["reason"]


def test_incompatible_definitions_block_evaluation():
    mismatched = profile(
        operational_definition=definition(
            "operational-definition", event="job failure observed"
        )
    )

    report = evaluate_stage2_corpus(rows(), mismatched)

    assert report.status == "blocked"
    assert report.pooling["status"] == "blocked"
    assert "incommensurable" in report.pooling["reason"]


def test_duplicate_change_across_rows_is_rejected():
    duplicate = replace(rows()[1], change_id=rows()[0].change_id)

    with pytest.raises(ValueError, match="change appears in multiple rows"):
        evaluate_stage2_corpus((rows()[0], duplicate, *rows()[2:]), profile())


def test_report_validation_rejects_tampering_and_excludes_scores():
    report = evaluate_stage2_corpus(rows(), profile())
    payload = report.to_dict()
    assert "change_score" not in json.dumps(payload)
    tampered = replace(report, counts={**report.counts, "test_labeled": 99})

    with pytest.raises(ValueError, match="report identity"):
        validate_stage2_corpus_evaluation_report(tampered)


@pytest.mark.parametrize(
    "change, message",
    [
        ({"candidate_id": ""}, "metadata is required"),
        ({"published_artifacts": ("same.json", "same.json")}, "artifacts"),
        ({"min_test_rows": 0}, "minimums"),
        ({"max_ece": 2.0}, "max_ece"),
    ],
)
def test_profile_rejects_invalid_gate_metadata(change, message):
    with pytest.raises(ValueError, match=message):
        replace(profile(), **change)


def test_invalid_gate_and_report_metadata_fail_closed():
    with pytest.raises(ValueError, match="gate status"):
        CorpusEvaluationGate("bad", "unknown", "invalid")
    with pytest.raises(ValueError, match="evaluation status"):
        CorpusEvaluationReport("id", "profile", "unknown", {}, {}, {}, ())
    with pytest.raises(ValueError, match="claim boundary"):
        CorpusEvaluationReport(
            "id", "profile", "blocked", {}, {}, {}, (), "wrong boundary"
        )
    assert CLAIM_BOUNDARY


@pytest.mark.parametrize(
    "mutation, message",
    [
        (lambda row: replace(row, prediction_fields={}), "missing predeclared"),
        (
            lambda row: replace(
                row, prediction_fields={**row.prediction_fields, "change_score": "high"}
            ),
            "numeric",
        ),
        (
            lambda row: replace(
                row, prediction_fields={**row.prediction_fields, "change_score": 2.0}
            ),
            r"in \[0, 1\]",
        ),
        (
            lambda row: replace(
                row,
                prediction_field_observed_at={
                    "operational_score": "2025-12-31T00:00:00+00:00"
                },
            ),
            "observation time",
        ),
        (
            lambda row: replace(
                row,
                prediction_field_observed_at={
                    "change_score": "2026-02-01T00:00:00+00:00",
                    "operational_score": "2025-12-31T00:00:00+00:00",
                },
            ),
            "post-score",
        ),
    ],
)
def test_prediction_fields_fail_closed(mutation, message):
    mutated = mutation(rows()[0])
    with pytest.raises(ValueError, match=message):
        evaluate_stage2_corpus((mutated, *rows()[1:]), profile())


def test_corpus_integrity_rejections_fail_closed():
    with pytest.raises(ValueError, match="rows are required"):
        evaluate_stage2_corpus((), profile())
    with pytest.raises(ValueError, match="rows must be unique"):
        evaluate_stage2_corpus((rows()[0], rows()[0]), profile())
    with pytest.raises(ValueError, match="system"):
        evaluate_stage2_corpus(
            (replace(rows()[0], system_id="other"), *rows()[1:]), profile()
        )
    with pytest.raises(ValueError, match="lane metadata"):
        evaluate_stage2_corpus(
            (replace(rows()[0], threshold_version="other"), *rows()[1:]), profile()
        )
    with pytest.raises(ValueError, match="lineage"):
        evaluate_stage2_corpus(
            (replace(rows()[0], observation_id=""), *rows()[1:]), profile()
        )
