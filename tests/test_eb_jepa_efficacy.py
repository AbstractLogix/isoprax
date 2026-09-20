from dataclasses import replace

import pytest

from isoprax import (
    EBJEPATrainingReport,
    EfficacyEvaluationProfile,
    EfficacyFamilyScores,
    EvidenceProvenance,
    FamilyEfficacyResult,
    evaluate_eb_jepa_efficacy,
)
from isoprax.external_anchor import ExternalAnchorVerification, stage2_statement_payload
from isoprax.identity import content_hash


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


def _claimable_family(family="change"):
    outcomes = tuple(index % 2 for index in range(800))
    return EfficacyFamilyScores(
        family=family,
        outcome_definition_id=f"{family}.outcome.v1",
        test_row_ids=tuple(f"{family}-{index}" for index in range(800)),
        outcomes=outcomes,
        candidate_scores=tuple(0.95 if outcome else 0.05 for outcome in outcomes),
        baseline_scores=(0.5,) * 800,
    )


def _claimable_splits():
    return {
        "train": ("train-1",),
        "calibration": ("cal-1",),
        "test": tuple(
            [f"change-{index}" for index in range(800)]
            + [f"operational-{index}" for index in range(800)]
        ),
    }


def _training_report():
    return EBJEPATrainingReport(
        pair_count=8,
        state_input_dim=10,
        change_input_dim=12,
        state_embedding_dim=6,
        requested_device="cpu",
        actual_device="cpu",
        torch_version="test",
        cuda_available=False,
        seed=17,
        epochs_completed=4,
        final_prediction_loss=0.1,
        final_variance_loss=0.2,
        final_covariance_loss=0.01,
        backend_identity="model-v1",
        state_representation_identity="state-v1",
    )


def _provenance(verified=False, corpus_identity="real-labeled-fixture-v1"):
    payload = {
        "corpus_identity": corpus_identity,
        "split_identity": "split-v1",
        "label_definition_identity": "labels-v1",
        "outcome_definition_ids": (
            "change.outcome.v1",
            "operational.outcome.v1",
        ),
        "predeclaration_commit": "commit-fixture-v1",
    }
    verification_factory = (
        ExternalAnchorVerification._from_verifier
        if verified
        else ExternalAnchorVerification
    )
    verification = verification_factory(
        status="verified" if verified else "unverified",
        anchor_type="sigstore_rekor_dsse",
        anchor_reference="rekor://fixture" if verified else "",
        bundle_path="fixture.json",
        signer_identity="fixture-signer" if verified else None,
        issuer="fixture-issuer" if verified else None,
        reason="fixture verification",
        statement=(
            stage2_statement_payload(
                content_hash(payload), payload["predeclaration_commit"]
            )
            if verified
            else None
        ),
    )
    return EvidenceProvenance(payload, content_hash(payload), verification=verification)


def _run_configuration():
    return {
        "backend_identity": "model-v1",
        "device": "cpu",
        "seed": 17,
        "epochs": 4,
        "batch_size": 4,
    }


def _evaluate(
    profile, *, split_row_ids, family_scores, model_identity="model-v1", **overrides
):
    values = {
        "training_completed": True,
        "training_report": _training_report(),
        "run_configuration": _run_configuration(),
    }
    values.update(overrides)
    return evaluate_eb_jepa_efficacy(
        profile,
        split_row_ids=split_row_ids,
        family_scores=family_scores,
        model_identity=model_identity,
        **values,
    )


def test_efficacy_is_not_claimable_without_completed_training():
    report = _evaluate(
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

    report = _evaluate(
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
    report = _evaluate(
        _profile(),
        split_row_ids=_splits(),
        family_scores=(_family(**kwargs), _family("operational")),
        model_identity="model-v1",
    )

    assert report.status == "not_claimable"
    assert any(reason in item for item in report.reasons)


def test_efficacy_supported_is_scoped_and_never_pooled():
    report = _evaluate(
        _profile(
            corpus_identity="real-labeled-fixture-v1",
            evidence_class="real_labeled",
            provenance=_provenance(True),
            min_test_rows=800,
            min_positive_events=50,
            min_negative_events=50,
        ),
        split_row_ids=_claimable_splits(),
        family_scores=(_claimable_family(), _claimable_family("operational")),
        model_identity="model-v1",
    )

    assert report.status == "efficacy_supported"
    assert set(report.family_results) == {"change", "operational"}
    assert report.pooled_score is None
    assert report.claim_scope.startswith("model-v1:real-labeled-fixture-v1:split-v1:")
    assert report.to_dict()["pooled_score"] is None


def test_synthetic_evidence_cannot_become_an_efficacy_claim():
    report = _evaluate(
        _profile(evidence_class="real_labeled", provenance=_provenance()),
        split_row_ids=_splits(),
        family_scores=(_family(), _family("operational")),
        model_identity="model-v1",
    )

    assert report.status == "not_claimable"
    assert any("provenance" in reason for reason in report.reasons)


def test_efficacy_rejects_missing_required_family_and_nonfinite_values():
    missing = _evaluate(
        _profile(),
        split_row_ids=_splits(),
        family_scores=(_family(),),
        model_identity="model-v1",
    )
    assert missing.status == "not_claimable"
    assert any("operational" in reason for reason in missing.reasons)

    nonfinite = _evaluate(
        _profile(required_families=("change",)),
        split_row_ids=_splits(),
        family_scores=(
            EfficacyFamilyScores(
                family="change",
                outcome_definition_id="change.v1",
                test_row_ids=("change-0", "change-1"),
                outcomes=(0, 1),
                candidate_scores=(float("nan"), 0.9),
                baseline_scores=(0.5, 0.5),
            ),
        ),
    )
    assert nonfinite.status == "not_claimable"
    assert any("finite" in reason for reason in nonfinite.reasons)


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


def test_efficacy_family_scores_report_malformed_alignment_and_labels():
    malformed = _evaluate(
        _profile(required_families=("change",)),
        split_row_ids=_splits(),
        family_scores=(
            EfficacyFamilyScores(
                family="change",
                outcome_definition_id="change.v1",
                test_row_ids=("change-0", "change-1"),
                outcomes=(0,),
                candidate_scores=(0.1, 0.9),
                baseline_scores=(0.5, 0.5),
            ),
        ),
    )
    assert any("aligned" in reason for reason in malformed.reasons)

    nonbinary = _evaluate(
        _profile(required_families=("change",)),
        split_row_ids=_splits(),
        family_scores=(
            EfficacyFamilyScores(
                family="change",
                outcome_definition_id="change.v1",
                test_row_ids=("change-0", "change-1"),
                outcomes=(0, 2),
                candidate_scores=(0.1, 0.9),
                baseline_scores=(0.5, 0.5),
            ),
        ),
    )
    assert any("binary" in reason for reason in nonbinary.reasons)

    nested_outcomes = _evaluate(
        _profile(required_families=("change",)),
        split_row_ids=_splits(),
        family_scores=(
            EfficacyFamilyScores(
                family="change",
                outcome_definition_id="change.v1",
                test_row_ids=("change-0", "change-1"),
                outcomes=((0, 1), (0, 1)),
                candidate_scores=(0.1, 0.9),
                baseline_scores=(0.5, 0.5),
            ),
        ),
    )
    assert any("one-dimensional" in reason for reason in nested_outcomes.reasons)

    duplicate = _evaluate(
        _profile(required_families=("change",)),
        split_row_ids=_splits(),
        family_scores=(
            EfficacyFamilyScores(
                family="change",
                outcome_definition_id="change.v1",
                test_row_ids=("change-0", "change-0"),
                outcomes=(0, 1),
                candidate_scores=(0.1, 0.9),
                baseline_scores=(0.5, 0.5),
            ),
        ),
    )
    assert any("unique" in reason for reason in duplicate.reasons)


def test_efficacy_rejects_missing_or_malformed_splits_and_duplicate_families():
    missing = _evaluate(
        _profile(),
        split_row_ids={"train": ("train-1",)},
        family_scores=(_family(), _family("operational")),
        model_identity="model-v1",
    )
    assert missing.status == "not_claimable"
    assert any("missing calibration" in reason for reason in missing.reasons)

    malformed = _evaluate(
        _profile(),
        split_row_ids=[],
        family_scores=(_family(), _family("operational")),
        model_identity="model-v1",
    )
    assert any("mapping" in reason for reason in malformed.reasons)

    duplicate = _evaluate(
        _profile(required_families=("change",)),
        split_row_ids=_splits(),
        family_scores=(_family(), _family()),
        model_identity="model-v1",
    )
    assert any("duplicate family" in reason for reason in duplicate.reasons)


def test_efficacy_rejects_family_rows_outside_test_and_one_class():
    outside = _evaluate(
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
    report = _evaluate(
        _profile(required_families=("change",)),
        split_row_ids=_splits(),
        family_scores=(one_class,),
        model_identity="model-v1",
    )
    assert any("only one class" in reason for reason in report.reasons)


def test_efficacy_rejects_invalid_declarations_and_report_tampering():
    invalid_profiles = (
        {"minimum_auc_gain": "bad"},
        {"minimum_auc_gain": float("nan")},
        {"provenance": "invalid"},
        {"required_families": ("",)},
    )
    for kwargs in invalid_profiles:
        with pytest.raises(ValueError):
            _profile(**kwargs)

    with pytest.raises(ValueError, match="family efficacy status"):
        FamilyEfficacyResult("change", "change.v1", "invalid", {}, {}, ())

    report = _evaluate(
        _profile(
            corpus_identity="real-labeled-fixture-v1",
            evidence_class="real_labeled",
            provenance=_provenance(True),
            min_test_rows=800,
            min_positive_events=50,
            min_negative_events=50,
        ),
        split_row_ids=_claimable_splits(),
        family_scores=(_claimable_family(), _claimable_family("operational")),
    )
    with pytest.raises(ValueError, match="report_identity"):
        replace(report, report_identity="tampered")
    with pytest.raises(ValueError, match="failure reasons"):
        replace(report, status="not_claimable", reasons=())
    with pytest.raises(ValueError, match="validated training report"):
        replace(report, training_report=None, training_report_identity="")
    bad_config = {"backend_identity": "other"}
    with pytest.raises(ValueError, match="backend identity"):
        replace(
            report,
            run_configuration=bad_config,
            run_configuration_identity=content_hash(bad_config),
        )
    forged_result = FamilyEfficacyResult(
        "change", "change.outcome.v1", "passed", {}, {}, ()
    )
    with pytest.raises(ValueError, match="every required family"):
        replace(
            report,
            family_results={
                "change": forged_result,
                "operational": report.family_results["operational"],
            },
        )
    forged_metrics = replace(
        report.family_results["change"],
        metrics={
            **dict(report.family_results["change"].metrics),
            "candidate_auc": 2.0,
        },
    )
    with pytest.raises(ValueError, match="every required family"):
        replace(
            report,
            family_results={
                "change": forged_metrics,
                "operational": report.family_results["operational"],
            },
        )
    forged_counts = replace(
        report.family_results["change"],
        counts={
            **dict(report.family_results["change"].counts),
            "test_rows": 801,
        },
    )
    with pytest.raises(ValueError, match="every required family"):
        replace(
            report,
            family_results={
                "change": forged_counts,
                "operational": report.family_results["operational"],
            },
        )


def test_efficacy_converts_invalid_controls_and_scores_to_reasons():
    profile = _profile(required_families=("change",))
    invalid_report = _evaluate(
        profile,
        split_row_ids={"train": None, "calibration": (), "test": None},
        family_scores=None,
    )
    assert invalid_report.status == "not_claimable"
    assert any("iterable" in reason for reason in invalid_report.reasons)

    invalid_report = _evaluate(
        profile,
        split_row_ids=_splits(),
        family_scores=(object(),),
    )
    assert any("EfficacyFamilyScores" in reason for reason in invalid_report.reasons)

    invalid_report = _evaluate(
        profile,
        split_row_ids=_splits(),
        family_scores=(
            EfficacyFamilyScores(
                family="change",
                outcome_definition_id="change.v1",
                test_row_ids=None,
                outcomes="01",
                candidate_scores=0.5,
                baseline_scores=(),
            ),
        ),
    )
    assert invalid_report.status == "not_claimable"
    assert any("missing" in reason for reason in invalid_report.reasons)

    invalid_report = _evaluate(
        profile,
        split_row_ids=_splits(),
        family_scores=(
            EfficacyFamilyScores(
                family="change",
                outcome_definition_id="change.v1",
                test_row_ids=("change-0", "change-1"),
                outcomes=(0, 1),
                candidate_scores=((0.1, 0.2), (0.3, 0.4)),
                baseline_scores=("bad", "values"),
            ),
        ),
    )
    assert any("one-dimensional" in reason for reason in invalid_report.reasons)


def test_efficacy_requires_training_and_run_provenance_for_a_claim():
    profile = _profile(
        corpus_identity="real-labeled-fixture-v1",
        evidence_class="real_labeled",
        provenance=_provenance(True),
        required_families=("change",),
    )
    kwargs = {
        "split_row_ids": _splits(),
        "family_scores": (_family(),),
        "model_identity": "model-v1",
    }
    missing_training = evaluate_eb_jepa_efficacy(profile, **kwargs)
    assert any("training report" in reason for reason in missing_training.reasons)
    mismatch = _evaluate(
        profile,
        **kwargs,
        training_report=replace(_training_report(), backend_identity="other"),
    )
    assert any("backend identity" in reason for reason in mismatch.reasons)
    missing_config = _evaluate(profile, **kwargs, run_configuration=None)
    assert any("run_configuration" in reason for reason in missing_config.reasons)
    invalid_config = _evaluate(profile, **kwargs, run_configuration={"bad": object()})
    assert any("canonical JSON" in reason for reason in invalid_config.reasons)
    wrong_config = _evaluate(
        profile, **kwargs, run_configuration={"backend_identity": "other"}
    )
    assert any("backend_identity" in reason for reason in wrong_config.reasons)
