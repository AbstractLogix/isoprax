from dataclasses import replace
from typing import TypeAlias

import pytest

import isoprax.admission as admission
import isoprax.replay_constraints as replay_constraints
from isoprax.admission import (
    AdmissionProfile,
    CalibrationEvidence,
    CorpusProvenance,
    CorpusRow,
    PredeclarationEvidence,
    SplitDefinition,
    evaluate_admission,
)
from isoprax.corpus_manifest import (
    CorpusManifest,
    build_corpus_manifest,
    validate_corpus_manifest,
)
from isoprax.replay_constraints import (
    ReplayConstraint,
    ReplayConstraintError,
    build_replay_constraints,
    validate_replay_constraints,
    validate_replay_constraints_dict,
)

SplitDefs: TypeAlias = tuple[
    SplitDefinition,
    SplitDefinition,
    SplitDefinition,
    SplitDefinition,
]


@pytest.fixture
def split_definitions() -> SplitDefs:
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


@pytest.fixture
def profile(
    split_definitions: SplitDefs,
) -> AdmissionProfile:
    return AdmissionProfile(
        allowed_prediction_fields=frozenset({"diff_size", "files_touched"}),
        forbidden_prediction_fields=frozenset(
            {"future_issue_link", "post_horizon_metric"}
        ),
        horizon_rule="fixed-24h-predeclared",
        horizon_frozen=True,
        adequacy_min_positives=0,
        adequacy_min_negatives=0,
        split_definitions=split_definitions,
        release_scope="manifest-only",
        thresholds_frozen=True,
        expected_system_id="svc-a",
    )


def _row(
    row_id: str = "r1",
    split: str = "train",
    score_time: str = "2026-01-02T00:00:00+00:00",
    outcome_class: str = "observed_positive",
    prediction_fields: dict[str, object] | None = None,
    linkage_bases: tuple[str, ...] = ("immutable_ids",),
    outcome_window_complete: bool = True,
    horizon_rule_used: str = "fixed-24h-predeclared",
    threshold_version: str = "slo-v1",
    system_id: str = "svc-a",
    change_id: str = "c1",
    change_group_id: str | None = None,
    censor_reason: str | None = None,
    build_succeeded: bool = True,
    deployment_succeeded: bool = True,
    monitoring_complete: bool = True,
) -> CorpusRow:
    return CorpusRow(
        row_id=row_id,
        system_id=system_id,
        change_id=change_id,
        deployment_id=f"d-{row_id}",
        observation_id=f"o-{row_id}",
        split=split,
        score_time=score_time,
        outcome_class=outcome_class,
        prediction_fields=prediction_fields or {"diff_size": 42, "files_touched": 3},
        linkage_bases=linkage_bases,
        outcome_window_complete=outcome_window_complete,
        horizon_rule_used=horizon_rule_used,
        threshold_version=threshold_version,
        change_group_id=change_group_id,
        censor_reason=censor_reason,
        prediction_field_observed_at={
            key: score_time
            for key in (prediction_fields or {"diff_size": 42, "files_touched": 3})
        },
        build_succeeded=build_succeeded,
        deployment_succeeded=deployment_succeeded,
        monitoring_complete=monitoring_complete,
    )


def test_lineage_gate_rejects_linkage_based_only_on_timestamp(
    profile: AdmissionProfile,
) -> None:
    rep = evaluate_admission(
        [_row(linkage_bases=("timestamp_proximity",))],
        profile,
    )
    g = {x.gate_id: x for x in rep.gate_results}["lineage_linkage"]
    assert not g.passed


def test_prediction_time_gate_rejects_forbidden_fields(
    profile: AdmissionProfile,
) -> None:
    rep = evaluate_admission(
        [_row(prediction_fields={"diff_size": 12, "future_issue_link": "x"})],
        profile,
    )
    g = {x.gate_id: x for x in rep.gate_results}["prediction_time_fields"]
    assert not g.passed


def test_prediction_time_gate_rejects_post_score_time_fields(
    profile: AdmissionProfile,
) -> None:
    row = _row()
    row = replace(
        row,
        prediction_field_observed_at={
            "diff_size": "2026-01-02T00:00:01+00:00",
            "files_touched": "2026-01-02T00:00:00+00:00",
        },
    )
    gate = {
        gate.gate_id: gate for gate in evaluate_admission([row], profile).gate_results
    }["prediction_time_fields"]
    assert not gate.passed


def test_outcome_gate_rejects_negative_without_complete_window(
    profile: AdmissionProfile,
) -> None:
    rep = evaluate_admission(
        [
            _row(
                outcome_class="observed_negative",
                outcome_window_complete=False,
            )
        ],
        profile,
    )
    g = {x.gate_id: x for x in rep.gate_results}["outcome_censoring"]
    assert not g.passed


def test_outcome_gate_requires_censor_reason(profile: AdmissionProfile) -> None:
    rep = evaluate_admission(
        [_row(outcome_class="censored", censor_reason=None)],
        profile,
    )
    g = {x.gate_id: x for x in rep.gate_results}["outcome_censoring"]
    assert not g.passed


def test_outcome_gate_requires_censoring_for_missing_build_evidence(
    profile: AdmissionProfile,
) -> None:
    gate = {
        gate.gate_id: gate
        for gate in evaluate_admission(
            [_row(build_succeeded=False)], profile
        ).gate_results
    }["outcome_censoring"]
    assert not gate.passed


def test_split_gate_rejects_row_outside_declared_window(
    profile: AdmissionProfile,
) -> None:
    rep = evaluate_admission(
        [_row(score_time="2026-02-01T00:00:00+00:00")],
        profile,
    )
    g = {x.gate_id: x for x in rep.gate_results}["split_followup"]
    assert not g.passed


def test_horizon_gate_rejects_nonfrozen_profile(split_definitions: SplitDefs) -> None:
    p = AdmissionProfile(
        allowed_prediction_fields=frozenset({"diff_size"}),
        forbidden_prediction_fields=frozenset(),
        horizon_rule="fixed-24h-predeclared",
        horizon_frozen=False,
        adequacy_min_positives=0,
        adequacy_min_negatives=0,
        split_definitions=split_definitions,
        release_scope="manifest-only",
        thresholds_frozen=True,
    )
    rep = evaluate_admission([_row(prediction_fields={"diff_size": 1})], p)
    g = {x.gate_id: x for x in rep.gate_results}["horizon_threshold_freeze"]
    assert not g.passed


def test_split_definitions_must_be_non_overlapping() -> None:
    with pytest.raises(ValueError):
        _ = AdmissionProfile(
            allowed_prediction_fields=frozenset({"diff_size"}),
            forbidden_prediction_fields=frozenset(),
            horizon_rule="fixed-24h-predeclared",
            horizon_frozen=True,
            adequacy_min_positives=0,
            adequacy_min_negatives=0,
            split_definitions=(
                SplitDefinition(
                    "train", "2026-01-01T00:00:00+00:00", "2026-01-08T00:00:00+00:00"
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
            ),
            release_scope="manifest-only",
            thresholds_frozen=True,
        )


def test_single_system_boundary_rejects_cross_system_rows(
    profile: AdmissionProfile,
) -> None:
    rep = evaluate_admission(
        [_row(row_id="r1"), _row(row_id="r2", system_id="svc-b")], profile
    )
    g = {x.gate_id: x for x in rep.gate_results}["single_system_boundary"]
    assert not g.passed


def test_cluster_by_change_rejects_same_change_across_splits(
    profile: AdmissionProfile,
) -> None:
    rows = [
        _row(row_id="r1", split="train", change_id="c-shared"),
        _row(
            row_id="r2",
            split="test",
            score_time="2026-01-22T00:00:00+00:00",
            change_id="c-shared",
        ),
    ]
    rep = evaluate_admission(rows, profile)
    g = {x.gate_id: x for x in rep.gate_results}["cluster_by_change"]
    assert not g.passed


def test_adequacy_gate_rejects_under_minimum_counts(
    split_definitions: SplitDefs,
) -> None:
    p = AdmissionProfile(
        allowed_prediction_fields=frozenset({"diff_size"}),
        forbidden_prediction_fields=frozenset(),
        horizon_rule="fixed-24h-predeclared",
        horizon_frozen=True,
        adequacy_min_positives=1,
        adequacy_min_negatives=1,
        split_definitions=split_definitions,
        release_scope="manifest-only",
        thresholds_frozen=True,
        expected_system_id="svc-a",
    )
    rep = evaluate_admission(
        [
            _row(
                row_id="r1",
                prediction_fields={"diff_size": 1},
                outcome_class="observed_positive",
            )
        ],
        p,
    )
    g = {x.gate_id: x for x in rep.gate_results}["adequacy"]
    assert not g.passed


def test_deterministic_output_for_identical_inputs(profile: AdmissionProfile) -> None:
    rows = [_row(row_id="r2"), _row(row_id="r1")]
    a = evaluate_admission(rows, profile)
    b = evaluate_admission(rows, profile)
    assert a == b


def test_admission_report_never_upgrades_conformance_class(
    profile: AdmissionProfile,
) -> None:
    rep = evaluate_admission([_row()], profile)
    assert "Semantic" not in rep.declarable_class
    assert "Full" not in rep.declarable_class


def test_manifest_contains_release_and_threshold_metadata(
    profile: AdmissionProfile,
) -> None:
    rep = evaluate_admission([_row()], profile)
    assert rep.manifest["release_scope"] == "manifest-only"
    assert rep.manifest["thresholds_frozen"] is True


def test_admission_requires_split_separated_calibration_and_safe_provenance(
    profile: AdmissionProfile,
) -> None:
    rows = [
        _row(row_id="train", split="train", score_time="2026-01-02T00:00:00+00:00"),
        _row(
            row_id="fit",
            split="calibration_fit",
            score_time="2026-01-08T00:00:00+00:00",
        ),
        _row(
            row_id="gate",
            split="calibration_gate",
            score_time="2026-01-15T00:00:00+00:00",
        ),
        _row(row_id="test", split="test", score_time="2026-01-22T00:00:00+00:00"),
    ]
    evidence_profile = replace(
        profile,
        calibration_evidence=CalibrationEvidence(("fit",), ("gate",)),
        predeclaration_evidence=PredeclarationEvidence(
            artifact_hash="sha256:abc",
            external_anchor_reference="https://anchor.example/abc",
            predeclared_at="2025-12-31T00:00:00+00:00",
            corpus_collection_started_at="2026-01-01T00:00:00+00:00",
        ),
        corpus_provenance=CorpusProvenance(
            source_system="deterministic-replay",
            uses_private_production_data=False,
            uses_privileged_telemetry=False,
        ),
        published_artifacts=("manifest.json",),
    )
    gates = {
        gate.gate_id: gate
        for gate in evaluate_admission(rows, evidence_profile).gate_results
    }
    assert gates["calibration_evidence"].passed
    assert gates["provenance"].passed

    unsafe = replace(
        evidence_profile,
        corpus_provenance=CorpusProvenance("private", True, False),
    )
    assert not {
        gate.gate_id: gate for gate in evaluate_admission(rows, unsafe).gate_results
    }["provenance"].passed


def test_manifest_build_and_validate_for_real_data_follow_on(
    profile: AdmissionProfile,
) -> None:
    rows = [_row(row_id="r1", split="train"), _row(row_id="r2", split="test")]
    manifest = build_corpus_manifest(
        rows,
        profile,
        source_system="svc-a",
        published_artifacts=("admission-manifest.json",),
        privacy_constraints=("no-private-telemetry",),
    )
    assert manifest.source_system == "svc-a"
    assert manifest.release_scope == "manifest-only"
    assert manifest.counts_by_split["train"]["observed_positive"] == 1
    assert manifest.counts_by_split["test"]["observed_positive"] == 1
    assert validate_corpus_manifest(manifest.to_dict()) is True


def test_replay_constraints_reject_cross_system_and_split_leakage(
    profile: AdmissionProfile,
) -> None:
    rows = [
        _row(row_id="r1", split="train", change_id="c-shared", system_id="svc-a"),
        _row(
            row_id="r2",
            split="test",
            score_time="2026-01-22T00:00:00+00:00",
            change_id="c-shared",
            system_id="svc-b",
        ),
    ]
    with pytest.raises(ReplayConstraintError):
        validate_replay_constraints(
            rows,
            split_definitions=profile.split_definitions,
            expected_system_id="svc-a",
            release_scope="manifest-only",
            threshold_frozen=True,
            horizon_frozen=True,
        )


def test_validate_corpus_manifest_requires_split_count_outcomes() -> None:
    invalid_manifest = {
        "source_system": "svc-a",
        "release_scope": "manifest-only",
        "horizon_rule": "fixed-24h-predeclared",
        "thresholds_frozen": True,
        "split_definitions": [
            {
                "name": "train",
                "start": "2026-01-01T00:00:00+00:00",
                "end": "2026-01-07T00:00:00+00:00",
            },
            {
                "name": "calibration_fit",
                "start": "2026-01-07T00:00:00+00:00",
                "end": "2026-01-14T00:00:00+00:00",
            },
            {
                "name": "calibration_gate",
                "start": "2026-01-14T00:00:00+00:00",
                "end": "2026-01-21T00:00:00+00:00",
            },
            {
                "name": "test",
                "start": "2026-01-21T00:00:00+00:00",
                "end": "2026-01-28T00:00:00+00:00",
            },
        ],
        "counts_by_split": {
            "train": {"observed_positive": 1},
            "calibration_fit": {
                "observed_positive": 0,
                "observed_negative": 0,
                "censored": 0,
            },
            "calibration_gate": {
                "observed_positive": 0,
                "observed_negative": 0,
                "censored": 0,
            },
            "test": {"observed_positive": 0, "observed_negative": 0, "censored": 0},
        },
    }
    with pytest.raises(ValueError):
        validate_corpus_manifest(invalid_manifest)


def test_validate_replay_constraints_dict_accepts_manifest_splits(
    profile: AdmissionProfile,
) -> None:
    rows = [
        _row(row_id="r1", split="train", change_id="c-train"),
        _row(
            row_id="r2",
            split="calibration_fit",
            score_time="2026-01-09T00:00:00+00:00",
            change_id="c-fit",
        ),
        _row(
            row_id="r3",
            split="calibration_gate",
            score_time="2026-01-16T00:00:00+00:00",
            change_id="c-gate",
        ),
        _row(
            row_id="r4",
            split="test",
            score_time="2026-01-22T00:00:00+00:00",
            change_id="c-test",
        ),
    ]
    manifest = {
        "splits": [
            {"name": s.name, "start": s.start, "end": s.end}
            for s in profile.split_definitions
        ],
        "release_scope": "manifest-only",
        "thresholds_frozen": True,
        "horizon_frozen": True,
    }
    validate_replay_constraints_dict(
        rows, manifest=manifest, expected_system_id="svc-a"
    )


@pytest.mark.parametrize(
    "kwargs, reason",
    (
        ({"release_scope": None}, "release_scope_metadata"),
        ({"threshold_frozen": False}, "threshold_freeze"),
        ({"horizon_frozen": False}, "frozen_split_boundaries"),
    ),
)
def test_replay_constraints_reject_missing_frozen_metadata(
    profile: AdmissionProfile, kwargs: dict[str, object], reason: str
) -> None:
    arguments: dict[str, object] = {"release_scope": "manifest-only"}
    arguments.update(kwargs)
    with pytest.raises(ReplayConstraintError, match=reason):
        validate_replay_constraints([_row()], split_definitions=None, **arguments)


def test_replay_constraint_dict_rejects_invalid_split_shapes(
    profile: AdmissionProfile,
) -> None:
    with pytest.raises(ValueError, match="list-like"):
        validate_replay_constraints_dict(
            [_row()], manifest={"splits": "invalid", "release_scope": "scope"}
        )
    with pytest.raises(ValueError, match="instances or dicts"):
        validate_replay_constraints_dict(
            [_row()], manifest={"splits": [object()], "release_scope": "scope"}
        )


def test_manifest_validation_rejects_missing_and_bad_typed_metadata() -> None:
    with pytest.raises(ValueError, match="missing required"):
        validate_corpus_manifest({})
    with pytest.raises(TypeError, match="mapping"):
        validate_corpus_manifest("not-a-manifest")  # type: ignore[arg-type]


def test_corpus_manifest_model_and_mapping_validation_cover_invalid_metadata(
    profile: AdmissionProfile,
) -> None:
    manifest = build_corpus_manifest(
        [], profile, source_system="svc-a", published_artifacts=("manifest.json",)
    )
    for kwargs, message in (
        ({"source_system": ""}, "source_system"),
        ({"release_scope": ""}, "release_scope"),
        ({"horizon_rule": ""}, "horizon_rule"),
        ({"split_definitions": ()}, "split_definitions"),
        ({"published_artifacts": ()}, "published_artifacts"),
        ({"counts_by_split": {}}, "counts_by_split"),
    ):
        with pytest.raises(ValueError, match=message):
            CorpusManifest(**{**manifest.__dict__, **kwargs})

    payload = manifest.to_dict()
    for key, value, message in (
        ("source_system", "", "source_system"),
        ("release_scope", "", "release_scope"),
        ("horizon_rule", "", "horizon_rule"),
        ("split_definitions", "bad", "split_definitions"),
        ("counts_by_split", "bad", "counts_by_split"),
    ):
        invalid = {**payload, key: value}
        with pytest.raises(ValueError, match=message):
            validate_corpus_manifest(invalid)


def test_manifest_and_replay_constraint_edge_cases(
    profile: AdmissionProfile, split_definitions: SplitDefs
) -> None:
    row = _row()
    manifest = build_corpus_manifest(
        [row], profile, source_system="svc-a", published_artifacts=("manifest.json",)
    )
    assert validate_corpus_manifest(manifest)
    with pytest.raises(ValueError, match="source_system"):
        build_corpus_manifest([row], profile, source_system=" ")
    with pytest.raises(ValueError, match="release_scope"):
        build_corpus_manifest([row], profile, source_system="svc-a", release_scope=" ")
    broken_counts = manifest.to_dict()
    broken_counts["counts_by_split"] = {
        name: {"observed_positive": 0, "observed_negative": 0, "censored": 0}
        for name in ("train", "calibration_fit", "calibration_gate", "test")
    }
    broken_counts["counts_by_split"]["train"] = []
    with pytest.raises(ValueError, match="must be a mapping"):
        validate_corpus_manifest(broken_counts)
    with pytest.raises(ValueError, match="ReplayConstraint.name"):
        ReplayConstraint(" ", "description")
    with pytest.raises(ReplayConstraintError, match="expected_system_id"):
        validate_replay_constraints(
            [_row(system_id="other")], expected_system_id="svc-a", release_scope="scope"
        )
    with pytest.raises(ReplayConstraintError, match="cross-system"):
        validate_replay_constraints(
            [_row(), _row(row_id="r2", system_id="other")], release_scope="scope"
        )
    with pytest.raises(ReplayConstraintError, match="missing required"):
        validate_replay_constraints(
            [row], split_definitions=split_definitions, release_scope="scope"
        )
    with pytest.raises(ReplayConstraintError, match="span multiple"):
        validate_replay_constraints(
            [row, _row(row_id="r2", split="test", change_id="c1")],
            split_definitions=(split_definitions[0], split_definitions[-1]),
            release_scope="scope",
        )
    with pytest.raises(ValueError, match="list-like"):
        validate_replay_constraints_dict(
            [row], manifest={"split_definitions": "bad", "release_scope": "scope"}
        )


def test_admission_model_and_gate_edge_cases(
    profile: AdmissionProfile, split_definitions: SplitDefs
) -> None:
    with pytest.raises(ValueError, match="invalid split"):
        SplitDefinition("bad", "2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00")
    with pytest.raises(ValueError, match="before"):
        SplitDefinition(
            "train", "2026-01-02T00:00:00+00:00", "2026-01-01T00:00:00+00:00"
        )
    with pytest.raises(ValueError, match="RFC 3339 UTC"):
        SplitDefinition("train", "2026-01-01T00:00:00", "2026-01-02T00:00:00+00:00")
    with pytest.raises(ValueError, match="invalid row split"):
        _row(split="bad")
    with pytest.raises(ValueError, match="invalid outcome"):
        _row(outcome_class="bad")
    with pytest.raises(ValueError, match="canonical order"):
        replace(profile, split_definitions=tuple(reversed(split_definitions)))
    with pytest.raises(ValueError, match="not overlap"):
        replace(
            profile,
            split_definitions=(
                split_definitions[0],
                replace(split_definitions[1], start="2026-01-06T00:00:00+00:00"),
                *split_definitions[2:],
            ),
        )
    assert not admission._gate_lineage_and_linkage([_row(linkage_bases=())]).passed
    assert not admission._gate_prediction_time_fields(
        [_row(prediction_fields={"bad": 1})], profile
    ).passed
    assert not admission._gate_prediction_time_fields(
        [
            replace(
                _row(prediction_fields={"diff_size": 1}),
                prediction_field_observed_at={},
            )
        ],
        profile,
    ).passed
    assert not admission._gate_outcome_classes_and_censoring(
        [_row(build_succeeded=False)]
    ).passed
    assert not admission._gate_outcome_classes_and_censoring(
        [_row(outcome_class="censored")]
    ).passed
    assert not admission._gate_split_and_followup(
        [_row(score_time="2026-02-01T00:00:00+00:00")], profile
    ).passed
    with pytest.raises(ValueError, match="RFC 3339 UTC"):
        _row(score_time="2026-01-01T00:00:00")
    assert not admission._gate_horizon_and_threshold_freeze(
        [_row(threshold_version="")], profile
    ).passed
    assert not admission._gate_calibration_evidence([], profile).passed
    assert not admission._gate_provenance_and_predeclaration(profile).passed
    assert not admission._gate_single_system_boundary(
        [_row(system_id="other")], profile
    ).passed
    assert not admission._gate_cluster_by_change(
        [_row(), _row(row_id="r2", split="test")]
    ).passed
    assert not admission._gate_adequacy(
        [], replace(profile, adequacy_min_positives=1)
    ).passed
    assert not admission._gate_manifest_metadata(profile).passed


def test_admission_remaining_fail_closed_branches(profile: AdmissionProfile) -> None:
    with pytest.raises(ValueError, match="horizon_rule"):
        replace(profile, horizon_rule="")
    with pytest.raises(ValueError, match="adequacy"):
        replace(profile, adequacy_min_positives=-1)
    with pytest.raises(ValueError, match="release_scope"):
        replace(profile, release_scope="")
    assert not admission._gate_lineage_and_linkage(
        [replace(_row(), deployment_id="")]
    ).passed
    assert not admission._gate_prediction_time_fields(
        [
            replace(
                _row(),
                prediction_field_observed_at={
                    "diff_size": "bad",
                    "files_touched": "bad",
                },
            )
        ],
        profile,
    ).passed
    assert not admission._gate_horizon_and_threshold_freeze(
        [_row(horizon_rule_used="other")], profile
    ).passed
    assert not admission._gate_calibration_evidence(
        [],
        replace(
            profile,
            calibration_evidence=CalibrationEvidence(("missing",), ("also-missing",)),
        ),
    ).passed
    assert not admission._gate_calibration_evidence(
        [_row()],
        replace(profile, calibration_evidence=CalibrationEvidence(("r1",), ("r1",))),
    ).passed
    provenance = CorpusProvenance("svc-a", False, False)
    assert not admission._gate_provenance_and_predeclaration(
        replace(profile, corpus_provenance=provenance)
    ).passed
    assert not admission._gate_provenance_and_predeclaration(
        replace(
            profile,
            corpus_provenance=provenance,
            predeclaration_evidence=PredeclarationEvidence("", "", "bad", "bad"),
        )
    ).passed
    assert not admission._gate_single_system_boundary(
        [_row(), _row(row_id="r2", system_id="other")],
        replace(profile, expected_system_id=None),
    ).passed
    assert admission._gate_manifest_metadata(
        replace(profile, published_artifacts=("manifest.json",))
    ).passed
    assert len(build_replay_constraints()) == 5
    assert replay_constraints._coerce_split_definitions(None) is None
    assert replay_constraints._coerce_split_definitions(profile.split_definitions[0])
    assert replay_constraints._coerce_split_definitions(
        [
            {
                "name": "train",
                "start": "2026-01-01T00:00:00+00:00",
                "end": "2026-01-02T00:00:00+00:00",
            }
        ]
    )


def test_split_gate_rejects_malformed_row_timestamp(profile: AdmissionProfile) -> None:
    row = _row()
    object.__setattr__(row, "score_time", "not-a-timestamp")

    gate = admission._gate_split_and_followup([row], profile)

    assert not gate.passed
    assert gate.failed_row_ids == ("r1",)


def test_parse_iso_rejects_empty_timestamp() -> None:
    with pytest.raises(ValueError, match="RFC 3339 UTC"):
        admission._parse_iso("")
