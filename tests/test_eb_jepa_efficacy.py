from dataclasses import replace

import pytest

import isoprax.efficacy as efficacy
from isoprax import (
    EBJEPATrainingReport,
    EfficacyEvaluationProfile,
    EfficacyFamilyScores,
    EvidenceProvenance,
    FamilyEfficacyResult,
    evaluate_eb_jepa_efficacy,
)
from isoprax.external_anchor import ExternalAnchorVerification
from isoprax.identity import content_hash
from tests.provenance_helpers import verified_anchor


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
    verification = (
        verified_anchor(payload)
        if verified
        else ExternalAnchorVerification(
            status="unverified",
            anchor_type="sigstore_rekor_dsse",
            anchor_reference="",
            bundle_path="fixture.json",
            signer_identity=None,
            issuer=None,
            reason="fixture verification",
        )
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


def _claimable_report():
    return _evaluate(
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


def test_efficacy_provenance_and_family_identity_gates():
    no_provenance = _profile(
        corpus_identity="real-labeled-fixture-v1", evidence_class="real_labeled"
    )
    report = _evaluate(
        no_provenance,
        split_row_ids=_splits(),
        family_scores=(_family(), _family("operational")),
    )
    assert any("provenance artifact" in reason for reason in report.reasons)

    mismatched = _profile(
        corpus_identity="real-labeled-fixture-v1",
        split_identity="split-v1",
        evidence_class="real_labeled",
        provenance=_provenance(True, corpus_identity="different-corpus"),
    )
    mismatch_report = _evaluate(
        mismatched,
        split_row_ids=_splits(),
        family_scores=(_family(), _family("operational")),
    )
    assert any("corpus identity" in reason for reason in mismatch_report.reasons)

    with pytest.raises(ValueError, match="family is required"):
        EfficacyFamilyScores("", "change.v1", (), (), (), ())
    with pytest.raises(ValueError, match="outcome_definition_id is required"):
        EfficacyFamilyScores("change", "", (), (), (), ())


def test_efficacy_family_result_validation_gates():
    report = _claimable_report()
    base = report.family_results["change"]

    cases = [
        (replace(base, family="other"), "identity is incomplete"),
        (replace(base, test_row_ids_digest="bad"), "digest is missing"),
        (
            replace(
                base,
                metrics={**dict(base.metrics), "candidate_auc": float("nan")},
            ),
            "non-finite",
        ),
        (
            replace(
                base,
                metrics={**dict(base.metrics), "auc_gain": 2.0},
            ),
            "outside",
        ),
        (
            replace(
                base,
                counts={
                    **dict(base.counts),
                    "test_rows": 799,
                    "negative_events": 399,
                },
            ),
            "test-row threshold",
        ),
        (
            replace(
                base,
                counts={
                    **dict(base.counts),
                    "test_rows": 849,
                    "positive_events": 49,
                    "negative_events": 800,
                },
            ),
            "positive-event threshold",
        ),
        (
            replace(
                base,
                counts={
                    **dict(base.counts),
                    "test_rows": 849,
                    "positive_events": 800,
                    "negative_events": 49,
                },
            ),
            "negative-event threshold",
        ),
        (
            replace(
                base,
                metrics={**dict(base.metrics), "candidate_auc": 0.5},
            ),
            "candidate AUC",
        ),
        (
            replace(
                base,
                metrics={**dict(base.metrics), "auc_gain": 0.0},
            ),
            "AUC gain",
        ),
        (
            replace(
                base,
                metrics={**dict(base.metrics), "candidate_ece": 0.3},
            ),
            "ECE",
        ),
        (
            replace(
                base,
                metrics={
                    **dict(base.metrics),
                    "candidate_brier": dict(base.metrics)["baseline_brier"] + 0.1,
                },
            ),
            "Brier",
        ),
    ]
    for result, reason in cases:
        assert any(
            reason.lower() in item.lower()
            for item in efficacy._passed_family_result_reasons(
                "change", result, report.profile
            )
        ), reason
        with pytest.raises(ValueError, match="every required family"):
            replace(
                report,
                family_results={
                    "change": result,
                    "operational": report.family_results["operational"],
                },
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
    assert report.family_results["change"].test_row_ids_digest == content_hash(
        tuple(f"change-{index}" for index in range(800))
    )


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

    invalid_report = _evaluate(
        profile,
        split_row_ids=_splits(),
        family_scores=(
            EfficacyFamilyScores(
                family="change",
                outcome_definition_id="change.v1",
                test_row_ids=("change-0", "change-1"),
                outcomes=(0, 1),
                candidate_scores=(10**1000, 0.9),
                baseline_scores=(0.5, 0.5),
            ),
        ),
    )
    assert any("numeric probabilities" in reason for reason in invalid_report.reasons)

    unverified = _provenance(False)
    unverified_anchor = replace(
        unverified.verification,
        statement={"malformed": object()},
    )
    malformed_provenance = EvidenceProvenance(
        unverified.payload,
        unverified.digest,
        verification=unverified_anchor,
    )
    malformed_profile = _profile(
        corpus_identity="real-labeled-fixture-v1",
        evidence_class="real_labeled",
        provenance=malformed_provenance,
    )
    malformed_report = _evaluate(
        malformed_profile,
        split_row_ids=_splits(),
        family_scores=(_family(), _family("operational")),
    )
    assert malformed_report.status == "not_claimable"


def test_efficacy_converts_missing_outcomes_and_split_duplicates(monkeypatch):
    profile = _profile(required_families=("change",))
    missing_outcomes = _evaluate(
        profile,
        split_row_ids=_splits(),
        family_scores=(
            EfficacyFamilyScores(
                family="change",
                outcome_definition_id="change.v1",
                test_row_ids=("change-0",),
                outcomes=(),
                candidate_scores=(0.5,),
                baseline_scores=(0.5,),
            ),
        ),
    )
    assert any("outcomes are missing" in reason for reason in missing_outcomes.reasons)

    invalid_outcomes = _evaluate(
        profile,
        split_row_ids=_splits(),
        family_scores=(
            EfficacyFamilyScores(
                family="change",
                outcome_definition_id="change.v1",
                test_row_ids=("change-0",),
                outcomes=("bad",),
                candidate_scores=(0.5,),
                baseline_scores=(0.5,),
            ),
        ),
    )
    assert any("binary integer labels" in reason for reason in invalid_outcomes.reasons)

    duplicate_splits = _splits()
    duplicate_splits["test"] = duplicate_splits["test"] + ("change-0",)
    duplicate_report = _evaluate(
        profile,
        split_row_ids=duplicate_splits,
        family_scores=(_family(),),
    )
    assert any("duplicated" in reason for reason in duplicate_report.reasons)

    original_hash = efficacy.content_hash

    def fail_row_digest(value):
        if isinstance(value, tuple) and value and value[0] == "change-0":
            raise ValueError("digest failure")
        return original_hash(value)

    monkeypatch.setattr(efficacy, "content_hash", fail_row_digest)
    result = efficacy._family_result(_family(), profile, set(_splits()["test"]))
    assert result.test_row_ids_digest == ""


def test_efficacy_report_constructor_guards():
    report = _claimable_report()
    with pytest.raises(ValueError, match="status is invalid"):
        replace(report, status="invalid")
    with pytest.raises(ValueError, match="pooled"):
        replace(report, pooled_score=0.5)
    with pytest.raises(ValueError, match="profile must"):
        replace(report, profile=object())
    with pytest.raises(ValueError, match="profile_identity"):
        replace(report, profile_identity="tampered")
    with pytest.raises(ValueError, match="EBJEPATrainingReport"):
        replace(report, training_report=object())
    with pytest.raises(ValueError, match="backend identity does not match"):
        replace(
            report,
            training_report=replace(report.training_report, backend_identity="other"),
        )
    with pytest.raises(ValueError, match="training_report_identity"):
        replace(report, training_report_identity="tampered")
    with pytest.raises(ValueError, match="validated training report"):
        replace(report, training_report=None, training_report_identity="present")
    with pytest.raises(ValueError, match="canonical JSON"):
        replace(report, run_configuration={"bad": object()})
    with pytest.raises(ValueError, match="run_configuration_identity"):
        replace(report, run_configuration_identity="tampered")
    with pytest.raises(ValueError, match="FamilyEfficacyResult"):
        replace(report, family_results={"change": object()})
    with pytest.raises(ValueError, match="run_configuration"):
        replace(
            report, run_configuration={}, run_configuration_identity=content_hash({})
        )

    synthetic_profile = _profile()
    with pytest.raises(ValueError, match="verified real-labeled"):
        replace(
            report,
            profile=synthetic_profile,
            profile_identity=synthetic_profile.identity,
        )


def test_efficacy_rejects_invalid_top_level_controls():
    with pytest.raises(ValueError, match="profile must"):
        evaluate_eb_jepa_efficacy(
            object(),
            split_row_ids=_splits(),
            family_scores=(),
            model_identity="model-v1",
        )
    with pytest.raises(ValueError, match="model_identity"):
        evaluate_eb_jepa_efficacy(
            _profile(),
            split_row_ids=_splits(),
            family_scores=(),
            model_identity="",
        )


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
