import pytest

from isoprax import (
    EfficacyEvaluationProfile,
    EfficacyFamilyScores,
    evaluate_eb_jepa_efficacy,
)


def _profile(**overrides):
    values = {
        "corpus_identity": "synthetic-corpus",
        "split_identity": "split-v1",
        "baseline_identity": "baseline-v1",
        "threshold_version": "thresholds-v1",
        "min_test_rows": 4,
        "min_positive_events": 2,
        "min_negative_events": 2,
        "minimum_auc_gain": 0.1,
        "minimum_candidate_auc": 0.6,
        "max_candidate_ece": 0.2,
        "max_brier_regression": 0.0,
        "required_families": ("change", "operational"),
    }
    values.update(overrides)
    return EfficacyEvaluationProfile(**values)


def _family(family="change", *, candidate=None, baseline=None, ids=None):
    return EfficacyFamilyScores(
        family=family,
        outcome_definition_id=f"{family}.outcome.v1",
        test_row_ids=tuple(ids or (f"{family}-{i}" for i in range(4))),
        outcomes=(0, 1, 0, 1),
        candidate_scores=tuple(candidate or (0.05, 0.95, 0.1, 0.9)),
        baseline_scores=tuple(baseline or (0.5, 0.5, 0.5, 0.5)),
    )


def _splits():
    return {
        "train": ("train-1",),
        "calibration": ("cal-1",),
        "test": tuple(
            ["change-0", "change-1", "change-2", "change-3"]
            + ["operational-0", "operational-1", "operational-2", "operational-3"]
        ),
    }


def test_efficacy_is_not_claimable_without_completed_training():
    report = evaluate_eb_jepa_efficacy(
        _profile(),
        split_row_ids=_splits(),
        family_scores=(_family(), _family("operational")),
        model_identity="model-v1",
        training_completed=False,
    )

    assert report.status == "not_claimable"
    assert any("training" in reason for reason in report.reasons)


def test_efficacy_rejects_overlapping_splits_before_metrics():
    splits = _splits()
    splits["calibration"] = ("change-0",)

    report = evaluate_eb_jepa_efficacy(
        _profile(),
        split_row_ids=splits,
        family_scores=(_family(), _family("operational")),
        model_identity="model-v1",
    )

    assert report.status == "not_claimable"
    assert any("overlap" in reason for reason in report.reasons)


@pytest.mark.parametrize(
    "kwargs,reason",
    [
        ({"candidate": (0.5, 0.5, 0.5, 0.5)}, "constant"),
        ({"candidate": (0.9, 0.8, 0.7, 0.6)}, "auc"),
        ({"baseline": (0.05, 0.95, 0.1, 0.9)}, "gain"),
    ],
)
def test_efficacy_reports_family_failure_reasons(kwargs, reason):
    report = evaluate_eb_jepa_efficacy(
        _profile(),
        split_row_ids=_splits(),
        family_scores=(_family(**kwargs), _family("operational")),
        model_identity="model-v1",
    )

    assert report.status == "not_claimable"
    assert any(reason in item for item in report.reasons)


def test_efficacy_supported_is_scoped_and_never_pooled():
    report = evaluate_eb_jepa_efficacy(
        _profile(evidence_class="real_labeled"),
        split_row_ids=_splits(),
        family_scores=(_family(), _family("operational")),
        model_identity="model-v1",
    )

    assert report.status == "efficacy_supported"
    assert set(report.family_results) == {"change", "operational"}
    assert report.pooled_score is None
    assert report.claim_scope == "model-v1:synthetic-corpus:split-v1"
    assert report.to_dict()["pooled_score"] is None


def test_synthetic_evidence_cannot_become_an_efficacy_claim():
    report = evaluate_eb_jepa_efficacy(
        _profile(),
        split_row_ids=_splits(),
        family_scores=(_family(), _family("operational")),
        model_identity="model-v1",
    )

    assert report.status == "not_claimable"
    assert any("synthetic" in reason for reason in report.reasons)


def test_efficacy_rejects_missing_required_family_and_nonfinite_values():
    missing = evaluate_eb_jepa_efficacy(
        _profile(),
        split_row_ids=_splits(),
        family_scores=(_family(),),
        model_identity="model-v1",
    )
    assert missing.status == "not_claimable"
    assert any("operational" in reason for reason in missing.reasons)

    with pytest.raises(ValueError, match="finite"):
        EfficacyFamilyScores(
            family="change",
            outcome_definition_id="change.v1",
            test_row_ids=("a", "b"),
            outcomes=(0, 1),
            candidate_scores=(float("nan"), 0.9),
            baseline_scores=(0.5, 0.5),
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"corpus_identity": ""},
        {"min_test_rows": 0},
        {"minimum_candidate_auc": 1.1},
        {"required_families": ("change", "change")},
        {"evidence_class": "gpu_smoke"},
    ],
)
def test_efficacy_profile_rejects_invalid_declarations(kwargs):
    with pytest.raises(ValueError):
        _profile(**kwargs)


def test_efficacy_family_scores_reject_malformed_alignment_and_labels():
    with pytest.raises(ValueError, match="aligned"):
        EfficacyFamilyScores(
            family="change",
            outcome_definition_id="change.v1",
            test_row_ids=("a", "b"),
            outcomes=(0,),
            candidate_scores=(0.1, 0.9),
            baseline_scores=(0.5, 0.5),
        )
    with pytest.raises(ValueError, match="binary"):
        EfficacyFamilyScores(
            family="change",
            outcome_definition_id="change.v1",
            test_row_ids=("a", "b"),
            outcomes=(0, 2),
            candidate_scores=(0.1, 0.9),
            baseline_scores=(0.5, 0.5),
        )
    with pytest.raises(ValueError, match="unique"):
        EfficacyFamilyScores(
            family="change",
            outcome_definition_id="change.v1",
            test_row_ids=("a", "a"),
            outcomes=(0, 1),
            candidate_scores=(0.1, 0.9),
            baseline_scores=(0.5, 0.5),
        )


def test_efficacy_rejects_missing_or_malformed_splits_and_duplicate_families():
    missing = evaluate_eb_jepa_efficacy(
        _profile(),
        split_row_ids={"train": ("train-1",)},
        family_scores=(_family(), _family("operational")),
        model_identity="model-v1",
    )
    assert missing.status == "not_claimable"
    assert any("missing calibration" in reason for reason in missing.reasons)

    malformed = evaluate_eb_jepa_efficacy(
        _profile(),
        split_row_ids=[],
        family_scores=(_family(), _family("operational")),
        model_identity="model-v1",
    )
    assert any("mapping" in reason for reason in malformed.reasons)

    duplicate = evaluate_eb_jepa_efficacy(
        _profile(required_families=("change",)),
        split_row_ids=_splits(),
        family_scores=(_family(), _family()),
        model_identity="model-v1",
    )
    assert any("duplicate family" in reason for reason in duplicate.reasons)


def test_efficacy_rejects_family_rows_outside_test_and_one_class():
    outside = evaluate_eb_jepa_efficacy(
        _profile(required_families=("change",)),
        split_row_ids=_splits(),
        family_scores=(
            _family(
                ids=("not-in-test-1", "not-in-test-2", "not-in-test-3", "not-in-test-4")
            ),
        ),
        model_identity="model-v1",
    )
    assert any("not contained" in reason for reason in outside.reasons)

    one_class = EfficacyFamilyScores(
        family="change",
        outcome_definition_id="change.v1",
        test_row_ids=("change-0", "change-1", "change-2", "change-3"),
        outcomes=(0, 0, 0, 0),
        candidate_scores=(0.1, 0.2, 0.3, 0.4),
        baseline_scores=(0.5, 0.5, 0.5, 0.5),
    )
    report = evaluate_eb_jepa_efficacy(
        _profile(required_families=("change",)),
        split_row_ids=_splits(),
        family_scores=(one_class,),
        model_identity="model-v1",
    )
    assert any("only one class" in reason for reason in report.reasons)
