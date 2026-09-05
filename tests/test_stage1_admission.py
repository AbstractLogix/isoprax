from typing import TypeAlias

import pytest

from isoprax.admission import (
    AdmissionProfile,
    CorpusRow,
    SplitDefinition,
    evaluate_admission,
)
from isoprax.corpus_manifest import build_corpus_manifest, validate_corpus_manifest
from isoprax.replay_constraints import (
    ReplayConstraintError,
    validate_replay_constraints,
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
