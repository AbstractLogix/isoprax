from __future__ import annotations

import pytest

from isoprax import (
    CandidateRecord,
    PredeclarationArtifact,
    build_replay_justification_exclusion,
    compute_predeclaration_hash,
    evaluate_predeclaration_provenance,
    record_exclusion_entry,
    screen_candidates,
    validate_predeclaration_artifact,
)


def test_screen_candidates_records_every_outcome_and_fail_order() -> None:
    candidates = [
        {
            "system_id": "bad-commit",
            "commit_supply": 5,
            "observed_positive_rate": 0.2,
            "licence_forbids_publication": False,
            "licence_forbids_redistribution": False,
            "sampled_build_success_rate": 0.98,
            "build_attempts": 25,
            "build_failures_clustered": False,
            "prediction_time_feature_allowlist_populatable": True,
        },
        {
            "system_id": "bad-license",
            "commit_supply": 100,
            "observed_positive_rate": 0.3,
            "licence_forbids_publication": True,
            "licence_forbids_redistribution": False,
            "sampled_build_success_rate": 0.99,
            "build_attempts": 25,
            "prediction_time_feature_allowlist_populatable": True,
        },
        {
            "system_id": "eligible",
            "commit_supply": 200,
            "observed_positive_rate": 0.3,
            "licence_forbids_publication": False,
            "licence_forbids_redistribution": False,
            "sampled_build_success_rate": 0.99,
            "build_attempts": 30,
            "prediction_time_feature_allowlist_populatable": True,
        },
    ]
    records = screen_candidates(candidates, adequacy_floor=20)
    assert len(records) == 3
    assert records[0].disqualifying_screen == "commit_supply"
    assert records[1].disqualifying_screen == "licence_terms"
    assert records[2].eligible is True
    assert records[1].screen_results[0].passed is True
    assert records[1].screen_results[1].passed is False


def test_predeclaration_hash_detects_tampering_and_rejects_window_derived_soak_rule() -> None:
    artifact = PredeclarationArtifact(
        artifact_id="plan-001",
        content="soak_duration=14d\npositive_event_definition=...\n",
        soak_duration="14d",
        soak_duration_rule="derive as 14d on training period only, not the observation window",
        positive_event_definition="observed_positive if outcome_window_complete and change_event_count >= 1",
        positive_event_thresholds={"positive_event_min": 1, "drift_threshold": 0.05},
        censoring_rule="drop rows with incomplete follow-up",
        drift_threshold=0.05,
        anchor_threshold=0.01,
        split_boundaries={"train": ("2026-01-01T00:00:00+00:00", "2026-01-07T00:00:00+00:00")},
        adequacy_floor=20,
        ablation_comparison_plan="compare baseline and drift-aware variants",
    )
    recorded_hash = compute_predeclaration_hash(artifact)
    assert validate_predeclaration_artifact(artifact, expected_hash=recorded_hash) is True
    tampered = PredeclarationArtifact(
        artifact_id="plan-001",
        content="soak_duration=15d\npositive_event_definition=...\n",
        soak_duration="15d",
        soak_duration_rule="derive as 14d on training period only, not the observation window",
        positive_event_definition="observed_positive if outcome_window_complete and change_event_count >= 1",
        positive_event_thresholds={"positive_event_min": 1, "drift_threshold": 0.05},
        censoring_rule="drop rows with incomplete follow-up",
        drift_threshold=0.05,
        anchor_threshold=0.01,
        split_boundaries={"train": ("2026-01-01T00:00:00+00:00", "2026-01-07T00:00:00+00:00")},
        adequacy_floor=20,
        ablation_comparison_plan="compare baseline and drift-aware variants",
    )
    with pytest.raises(ValueError):
        validate_predeclaration_artifact(tampered, expected_hash=recorded_hash)

    window_derived = PredeclarationArtifact(
        artifact_id="plan-window-bad",
        content="soak_duration=7d\n",
        soak_duration="7d",
        soak_duration_rule="derive from the same observation window it bounds",
        positive_event_definition="observed_positive if outcome_window_complete and change_event_count >= 1",
        positive_event_thresholds={"positive_event_min": 1},
        censoring_rule="drop rows with incomplete follow-up",
        drift_threshold=0.05,
        anchor_threshold=0.01,
        split_boundaries={"train": ("2026-01-01T00:00:00+00:00", "2026-01-07T00:00:00+00:00")},
        adequacy_floor=20,
        ablation_comparison_plan="compare baseline and drift-aware variants",
    )
    with pytest.raises(ValueError):
        validate_predeclaration_artifact(window_derived)


def test_predeclaration_provenance_requires_anchor_and_ancestry() -> None:
    artifact = PredeclarationArtifact(
        artifact_id="plan-001",
        content="frozen",
        soak_duration="14d",
        soak_duration_rule="derive 14d from training-period-only data, not the observation window",
        positive_event_definition="observed_positive if outcome_window_complete",
        positive_event_thresholds={"positive_event_min": 1},
        censoring_rule="drop rows with incomplete follow-up",
        drift_threshold=0.05,
        anchor_threshold=0.01,
        split_boundaries={"train": ("2026-01-01T00:00:00+00:00", "2026-01-07T00:00:00+00:00")},
        adequacy_floor=20,
        ablation_comparison_plan="compare baseline and drift-aware variants",
    )
    recorded_hash = compute_predeclaration_hash(artifact)
    provenance = evaluate_predeclaration_provenance(
        artifact,
        artifact_hash=recorded_hash,
        predeclaration_commit="commit-predecl",
        corpus_data_commits=("commit-c1", "commit-c2"),
        external_anchor={"anchor_type": "remote_push", "anchor_reference": "https://example.com/repo"},
        remote_configured=True,
        repository_pushed=True,
        commit_timestamps={
            "commit-predecl": "2026-01-02T00:00:00+00:00",
            "commit-c1": "2026-01-03T00:00:00+00:00",
            "commit-c2": "2026-01-04T00:00:00+00:00",
        },
    )
    assert provenance.anchored is True
    assert provenance.ancestry_ok is True

    with pytest.raises(ValueError):
        evaluate_predeclaration_provenance(
            artifact,
            artifact_hash=recorded_hash,
            predeclaration_commit="commit-predecl",
            corpus_data_commits=("commit-old",),
            external_anchor={"anchor_type": "remote_push", "anchor_reference": "https://example.com/repo"},
            remote_configured=True,
            repository_pushed=True,
            commit_timestamps={
                "commit-predecl": "2026-01-10T00:00:00+00:00",
                "commit-old": "2026-01-05T00:00:00+00:00",
            },
        )


def test_exclusion_entries_stay_structural_not_pending() -> None:
    no_change = record_exclusion_entry(
        "dataset-no-change",
        exclusion_type="structural_no_change_events",
        reason="This dataset has no Change-family event exists to condition on; it is excluded structurally and remains available only as a baseline reference.",
        residual_use="Structural-conformance baseline reference",
        pending=False,
    )
    assert no_change.pending is False
    assert "pending" not in no_change.reason.lower()

    mismatch = record_exclusion_entry(
        "dataset-mismatch",
        exclusion_type="commensurability_mismatch",
        reason="This dataset fails Isoprax v0.3 §5.6 because both families derive labels from different observation processes; calibrating either or both sides does not resolve the exclusion.",
        residual_use="Structural-conformance or baseline reference only",
        pending=False,
    )
    assert mismatch.residual_use == "Structural-conformance or baseline reference only"

    replay_justification = build_replay_justification_exclusion("dataset-shared-process")
    assert replay_justification.cited_spec == "Isoprax v0.3 §5.6"
    assert "paired dataset" in replay_justification.reason.lower()
