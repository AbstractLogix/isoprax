import json
from dataclasses import replace

import pytest

from isoprax.admission import (
    AdmissionProfile,
    CalibrationEvidence,
    CorpusProvenance,
    CorpusRow,
    PredeclarationEvidence,
    SplitDefinition,
    evaluate_admission,
)
from isoprax.commensurability import OutcomeDefinition
from isoprax.evaluation import CONFORMANCE_MIN_EVENTS
from isoprax.per_family_evaluation import (
    PerFamilyEvaluationProfile,
    evaluate_per_family,
)


def split_definitions() -> tuple[
    SplitDefinition,
    SplitDefinition,
    SplitDefinition,
    SplitDefinition,
]:
    return (
        SplitDefinition(
            "train", "2026-01-01T00:00:00+00:00", "2026-01-07T00:00:00+00:00"
        ),
        SplitDefinition(
            "calibration_fit",
            "2026-01-07T00:00:00+00:00",
            "2026-01-14T00:00:00+00:00",
        ),
        SplitDefinition(
            "calibration_gate",
            "2026-01-14T00:00:00+00:00",
            "2026-01-21T00:00:00+00:00",
        ),
        SplitDefinition(
            "test", "2026-01-21T00:00:00+00:00", "2026-01-28T00:00:00+00:00"
        ),
    )


def profile(**changes) -> AdmissionProfile:
    base = AdmissionProfile(
        allowed_prediction_fields=frozenset({"risk_score", "diff_size"}),
        forbidden_prediction_fields=frozenset({"future_field"}),
        horizon_rule="fixed-24h-predeclared",
        horizon_frozen=True,
        adequacy_min_positives=0,
        adequacy_min_negatives=0,
        split_definitions=split_definitions(),
        release_scope="public synthetic replay evidence",
        thresholds_frozen=True,
        expected_system_id="svc-a",
        calibration_evidence=CalibrationEvidence(("fit-1",), ("gate-1", "gate-2")),
        predeclaration_evidence=PredeclarationEvidence(
            artifact_hash="sha256:abc",
            external_anchor_reference="https://anchor.example/test",
            predeclared_at="2025-12-31T00:00:00+00:00",
            corpus_collection_started_at="2026-01-01T00:00:00+00:00",
        ),
        corpus_provenance=CorpusProvenance(
            source_system="svc-a",
            uses_private_production_data=False,
            uses_privileged_telemetry=False,
        ),
        published_artifacts=("manifest.json",),
    )
    return replace(base, **changes)


def row(
    row_id: str,
    split: str,
    score_time: str,
    outcome_class: str,
    risk_score: float = 0.5,
) -> CorpusRow:
    return CorpusRow(
        row_id=row_id,
        system_id="svc-a",
        change_id=f"change-{row_id}",
        deployment_id=f"deployment-{row_id}",
        observation_id=f"obs-{row_id}",
        split=split,
        score_time=score_time,
        outcome_class=outcome_class,
        prediction_fields={"risk_score": risk_score, "diff_size": 1},
        linkage_bases=("immutable_ids",),
        outcome_window_complete=True,
        horizon_rule_used="fixed-24h-predeclared",
        threshold_version="slo-v1",
        change_group_id=f"group-{row_id}",
        censor_reason="monitoring gap" if outcome_class == "censored" else None,
        prediction_field_observed_at={
            "risk_score": score_time,
            "diff_size": score_time,
        },
        build_succeeded=True,
        deployment_succeeded=True,
        monitoring_complete=True,
    )


def evaluation_profile(**changes) -> PerFamilyEvaluationProfile:
    base = PerFamilyEvaluationProfile(
        family="change",
        outcome_definition=OutcomeDefinition(
            id="defect_linked_fix",
            event="post-release defect linked to change",
            observation_process="ticket-linking",
            window="14d",
            thresholds="severity>=high",
        ),
        score_field="risk_score",
        predeclared_threshold_version="slo-v1",
    )
    return replace(base, **changes)


def admitted_rows() -> list[CorpusRow]:
    return [
        row("train-1", "train", "2026-01-02T00:00:00+00:00", "observed_positive", 0.8),
        row(
            "fit-1",
            "calibration_fit",
            "2026-01-08T00:00:00+00:00",
            "observed_negative",
            0.3,
        ),
        row(
            "gate-1",
            "calibration_gate",
            "2026-01-15T00:00:00+00:00",
            "observed_positive",
            0.7,
        ),
        row(
            "gate-2",
            "calibration_gate",
            "2026-01-16T00:00:00+00:00",
            "observed_negative",
            0.4,
        ),
        row("test-1", "test", "2026-01-22T00:00:00+00:00", "observed_positive", 0.9),
        row("test-2", "test", "2026-01-23T00:00:00+00:00", "observed_negative", 0.2),
    ]


def calibrated_gate_rows() -> list[CorpusRow]:
    """Enough calibration-gate events to satisfy the library conformance minimum."""
    return [
        row(
            f"gate-{index:03d}",
            "calibration_gate",
            "2026-01-15T00:00:00+00:00",
            "observed_positive" if index % 2 == 0 else "observed_negative",
            0.5,
        )
        for index in range(CONFORMANCE_MIN_EVENTS)
    ]


def calibrated_rows() -> list[CorpusRow]:
    return [
        item for item in admitted_rows() if item.split != "calibration_gate"
    ] + calibrated_gate_rows()


def calibrated_profile() -> AdmissionProfile:
    return replace(
        profile(),
        calibration_evidence=CalibrationEvidence(
            ("fit-1",), tuple(item.row_id for item in calibrated_gate_rows())
        ),
    )


def test_deterministic_per_family_evaluation_for_admitted_rows():
    rows = calibrated_rows()
    admission_profile = calibrated_profile()
    admission = evaluate_admission(rows, admission_profile)
    left = evaluate_per_family(rows, admission_profile, admission, evaluation_profile())
    right = evaluate_per_family(
        list(reversed(rows)), admission_profile, admission, evaluation_profile()
    )

    assert left == right
    assert left.status == "inconclusive"
    assert left.calibration["status"] == "uncalibrated"
    assert any(
        item.category == "calibration_conformance" and "discrimination" in item.reason
        for item in left.unavailable_evidence
    )
    assert left.family == "change"
    assert left.outcome_definition_id == "defect_linked_fix"
    assert "Semantic" in left.claim_boundary
    assert set(left.metrics) == {"brier_score", "ece", "positive_rate"}


def test_report_evidence_mappings_are_read_only():
    rows = calibrated_rows()
    admission_profile = calibrated_profile()
    report = evaluate_per_family(
        rows,
        admission_profile,
        evaluate_admission(rows, admission_profile),
        evaluation_profile(),
    )

    with pytest.raises(TypeError):
        report.metrics["brier_score"] = 0.0
    with pytest.raises(TypeError):
        report.counts["rows"] = 0
    with pytest.raises(TypeError):
        report.calibration["passes"] = True
    with pytest.raises(TypeError):
        report.uncertainty["positive_rate_ci_low"] = 0.0

    serialized = report.to_dict()
    serialized["counts"]["rows"] = 0
    assert report.counts["rows"] == len(rows)
    assert json.loads(json.dumps(report.to_dict()))["counts"]["rows"] == len(rows)


def test_returns_blocked_when_admission_fails():
    rows = admitted_rows()
    bad_profile = replace(profile(), adequacy_min_positives=2)
    blocked_admission = evaluate_admission(rows, bad_profile)

    report = evaluate_per_family(
        rows, bad_profile, blocked_admission, evaluation_profile()
    )

    assert report.status == "blocked"
    assert report.metrics == {}
    assert any(
        item.category == "admission_report" for item in report.unavailable_evidence
    )


def test_reports_inconclusive_when_test_rows_have_no_observed_outcomes():
    rows = [
        replace(item, outcome_class="censored", censor_reason="artifact missing")
        if item.split == "test"
        else item
        for item in admitted_rows()
    ]
    admission = evaluate_admission(rows, profile())

    report = evaluate_per_family(rows, profile(), admission, evaluation_profile())

    assert report.status == "inconclusive"
    assert report.metrics == {}
    assert any(
        item.category == "test_labeled_outcomes" for item in report.unavailable_evidence
    )


def test_rejects_post_hoc_threshold_mismatch_and_missing_predeclaration():
    rows = admitted_rows()
    admission = evaluate_admission(rows, profile())

    with pytest.raises(ValueError, match="threshold version"):
        evaluate_per_family(
            [replace(rows[0], threshold_version="other"), *rows[1:]],
            profile(),
            admission,
            evaluation_profile(),
        )
    with pytest.raises(ValueError, match="predeclaration evidence"):
        evaluate_per_family(
            rows,
            replace(profile(), predeclaration_evidence=None),
            admission,
            evaluation_profile(),
        )


def test_rejects_non_split_isolated_calibration_evidence():
    rows = admitted_rows()
    good_profile = profile()
    admission = evaluate_admission(rows, good_profile)
    bad_profile = replace(
        good_profile,
        calibration_evidence=CalibrationEvidence(("train-1",), ("gate-1",)),
    )

    with pytest.raises(ValueError, match="calibration fit evidence"):
        evaluate_per_family(rows, bad_profile, admission, evaluation_profile())


def test_rejects_missing_or_invalid_score_fields():
    rows = admitted_rows()
    admission = evaluate_admission(rows, profile())

    with pytest.raises(ValueError, match="missing predeclared score field"):
        evaluate_per_family(
            [
                replace(rows[4], prediction_fields={"diff_size": 1}),
                *rows[:4],
                *rows[5:],
            ],
            profile(),
            admission,
            evaluation_profile(),
        )
    with pytest.raises(ValueError, match=r"in \[0, 1\]"):
        evaluate_per_family(
            [
                replace(rows[4], prediction_fields={"risk_score": 1.2, "diff_size": 1}),
                *rows[:4],
                *rows[5:],
            ],
            profile(),
            admission,
            evaluation_profile(),
        )


def test_profile_validation_paths():
    with pytest.raises(ValueError, match="metadata"):
        _ = PerFamilyEvaluationProfile(
            family="",
            outcome_definition=OutcomeDefinition("x", "e", "p", "w", "t"),
            score_field="risk_score",
            predeclared_threshold_version="slo-v1",
        )
    with pytest.raises(ValueError, match="canonical"):
        _ = PerFamilyEvaluationProfile(
            family="change",
            outcome_definition=OutcomeDefinition("x", "e", "p", "w", "t"),
            score_field="risk_score",
            predeclared_threshold_version="slo-v1",
            predeclared_metrics=("brier_score", "unknown"),
        )


def test_additional_fail_closed_paths_and_report_serialization():
    rows = admitted_rows()
    good_profile = profile()
    admission = evaluate_admission(rows, good_profile)

    with pytest.raises(ValueError, match="evaluation rows are required"):
        evaluate_per_family([], good_profile, admission, evaluation_profile())

    with pytest.raises(ValueError, match="post-hoc thresholds or horizon"):
        evaluate_per_family(
            rows,
            replace(good_profile, horizon_frozen=False),
            admission,
            evaluation_profile(),
        )

    with pytest.raises(ValueError, match="must be unique"):
        evaluate_per_family(
            rows + [rows[0]], good_profile, admission, evaluation_profile()
        )

    with pytest.raises(ValueError, match="references unknown rows"):
        evaluate_per_family(
            rows,
            replace(
                good_profile,
                calibration_evidence=CalibrationEvidence(("fit-1",), ("missing-gate",)),
            ),
            admission,
            evaluation_profile(),
        )

    with pytest.raises(ValueError, match="calibration gate evidence"):
        evaluate_per_family(
            rows,
            replace(
                good_profile,
                calibration_evidence=CalibrationEvidence(("fit-1",), ("train-1",)),
            ),
            admission,
            evaluation_profile(),
        )

    with pytest.raises(ValueError, match="score field must be numeric"):
        evaluate_per_family(
            [
                replace(
                    rows[4],
                    prediction_fields={"risk_score": "0.3", "diff_size": 1},
                ),
                *rows[:4],
                *rows[5:],
            ],
            good_profile,
            admission,
            evaluation_profile(),
        )

    report = evaluate_per_family(rows, good_profile, admission, evaluation_profile())
    assert report.to_dict()["claim_scope"] == "stage1_per_family_evaluation_only"


def test_inconclusive_and_uncalibrated_when_calibration_or_test_evidence_missing():
    rows = admitted_rows()
    good_profile = profile()

    no_test_rows = [item for item in rows if item.split != "test"]
    no_test_report = evaluate_per_family(
        no_test_rows,
        good_profile,
        evaluate_admission(no_test_rows, good_profile),
        evaluation_profile(),
    )
    assert no_test_report.status == "inconclusive"
    assert any(
        item.category == "test_rows" for item in no_test_report.unavailable_evidence
    )

    gate_censored_rows = [
        replace(item, outcome_class="censored", censor_reason="missing")
        if item.split == "calibration_gate"
        else item
        for item in rows
    ]
    gate_censored_report = evaluate_per_family(
        gate_censored_rows,
        good_profile,
        evaluate_admission(gate_censored_rows, good_profile),
        evaluation_profile(),
    )
    assert gate_censored_report.status == "inconclusive"
    assert gate_censored_report.calibration["status"] == "uncalibrated"
    assert any(
        item.category == "calibration_diagnostics"
        for item in gate_censored_report.unavailable_evidence
    )


def test_calibration_applies_library_minimum_event_rule():
    rows = admitted_rows()
    admission = evaluate_admission(rows, profile())

    report = evaluate_per_family(rows, profile(), admission, evaluation_profile())

    assert report.calibration["passes"] is False
    assert report.calibration["status"] == "uncalibrated"
    assert "insufficient labeled events" in report.calibration["reason"]
    assert report.calibration["n_events"] == 2
    assert report.status == "inconclusive"
    assert any(
        item.category == "calibration_conformance"
        for item in report.unavailable_evidence
    )


def test_rejects_duplicate_rows_without_calibration_evidence():
    rows = admitted_rows()
    no_evidence_profile = replace(profile(), calibration_evidence=None)
    admission = evaluate_admission(rows, no_evidence_profile)

    with pytest.raises(ValueError, match="must be unique"):
        evaluate_per_family(
            rows + [rows[4]], no_evidence_profile, admission, evaluation_profile()
        )


def test_blocks_corpora_whose_admission_lacks_calibration_evidence():
    rows = admitted_rows()
    no_evidence_profile = replace(profile(), calibration_evidence=None)

    report = evaluate_per_family(
        rows,
        no_evidence_profile,
        evaluate_admission(rows, no_evidence_profile),
        evaluation_profile(),
    )

    assert report.status == "blocked"
    assert any(
        item.category == "admission_report" for item in report.unavailable_evidence
    )


def test_rejects_boolean_score_field():
    rows = admitted_rows()
    admission = evaluate_admission(rows, profile())

    with pytest.raises(ValueError, match="score field must be numeric"):
        evaluate_per_family(
            [
                replace(
                    rows[4], prediction_fields={"risk_score": True, "diff_size": 1}
                ),
                *rows[:4],
                *rows[5:],
            ],
            profile(),
            admission,
            evaluation_profile(),
        )


def test_omits_uncertainty_without_observed_test_outcomes():
    rows = [
        replace(item, outcome_class="censored", censor_reason="artifact missing")
        if item.split == "test"
        else item
        for item in admitted_rows()
    ]
    admission = evaluate_admission(rows, profile())

    report = evaluate_per_family(rows, profile(), admission, evaluation_profile())

    assert report.uncertainty == {}
    assert report.counts["censored"] == 2


def test_evaluation_identity_binds_corpus_and_profile():
    rows = admitted_rows()
    admission = evaluate_admission(rows, profile())
    baseline = evaluate_per_family(rows, profile(), admission, evaluation_profile())

    unused_train_score = [
        replace(item, prediction_fields={"risk_score": 0.6, "diff_size": 1})
        if item.split == "train"
        else item
        for item in rows
    ]
    rescored = evaluate_per_family(
        unused_train_score,
        profile(),
        evaluate_admission(unused_train_score, profile()),
        evaluation_profile(),
    )

    assert rescored.metrics == baseline.metrics
    assert rescored.evaluation_identity != baseline.evaluation_identity

    other_field = evaluate_per_family(
        rows,
        profile(),
        admission,
        evaluation_profile(predeclared_metrics=("brier_score",)),
    )
    assert other_field.evaluation_identity != baseline.evaluation_identity


def test_blocked_identity_and_counts_reflect_the_corpus():
    rows = admitted_rows()
    bad_profile = replace(profile(), adequacy_min_positives=2)
    full_report = evaluate_per_family(
        rows, bad_profile, evaluate_admission(rows, bad_profile), evaluation_profile()
    )

    fewer = [item for item in rows if item.row_id != "test-2"]
    fewer_report = evaluate_per_family(
        fewer, bad_profile, evaluate_admission(fewer, bad_profile), evaluation_profile()
    )

    assert full_report.counts["test_rows"] == 2
    assert fewer_report.counts["test_rows"] == 1
    assert set(full_report.counts) == {"rows", "test_rows", "test_observed", "censored"}
    assert full_report.evaluation_identity != fewer_report.evaluation_identity


def test_rejects_admission_report_not_bound_to_rows_and_profile():
    rows = admitted_rows()
    foreign = evaluate_admission(
        [item for item in rows if item.split != "test"], profile()
    )

    with pytest.raises(ValueError, match="admission report does not match"):
        evaluate_per_family(rows, profile(), foreign, evaluation_profile())

    tainted = [replace(rows[4], system_id="svc-b"), *rows[:4], *rows[5:]]
    assert evaluate_admission(tainted, profile()).admissible is False
    with pytest.raises(ValueError, match="admission report does not match"):
        evaluate_per_family(
            tainted,
            profile(),
            evaluate_admission(rows, profile()),
            evaluation_profile(),
        )


def test_rejects_duplicate_calibration_evidence_row_ids():
    rows = admitted_rows()
    duplicated = replace(
        profile(),
        calibration_evidence=CalibrationEvidence(
            ("fit-1",), ("gate-1", "gate-1", "gate-2")
        ),
    )

    with pytest.raises(ValueError, match="calibration evidence row ids must be unique"):
        evaluate_per_family(
            rows,
            duplicated,
            evaluate_admission(rows, duplicated),
            evaluation_profile(),
        )
