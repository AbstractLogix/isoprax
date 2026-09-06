from __future__ import annotations

import subprocess

import pytest

from isoprax import (
    PredeclarationArtifact,
    build_replay_justification_exclusion,
    compute_predeclaration_hash,
    derive_build_floor,
    evaluate_predeclaration_provenance,
    record_exclusion_entry,
    screen_candidates,
    screen_early_candidate,
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
            "sampled_prediction_fields": {"c1": {"commit_message": "x"}},
        },
        {
            "system_id": "bad-license",
            "commit_supply": 100,
            "observed_positive_rate": 0.3,
            "licence_forbids_publication": True,
            "licence_forbids_redistribution": False,
            "sampled_build_success_rate": 0.99,
            "build_attempts": 25,
            "sampled_prediction_fields": {"c2": {"commit_message": "x"}},
        },
        {
            "system_id": "eligible",
            "commit_supply": 200,
            "observed_positive_rate": 0.3,
            "licence_forbids_publication": False,
            "licence_forbids_redistribution": False,
            "sampled_build_success_rate": 0.99,
            "build_attempts": 30,
            "sampled_prediction_fields": {"c3": {"commit_message": "x"}},
        },
    ]
    records = screen_candidates(
        candidates,
        adequacy_floor=20,
        reference_build_success_rates=[0.99] * 200,
        reference_project_id="unrelated-stable-project",
        prediction_time_feature_allowlist={"commit_message"},
    )
    assert len(records) == 3
    assert records[0].disqualifying_screen == "commit_supply"
    assert len(records[0].screen_results) == 1
    assert records[1].disqualifying_screen == "licence_terms"
    assert len(records[1].screen_results) == 2
    assert records[2].eligible is True
    assert len(records[2].screen_results) == 4
    assert records[1].screen_results[0].passed is True
    assert records[1].screen_results[1].passed is False


def test_predeclaration_hash_detects_tampering_and_rejects_window_derived_soak_rule() -> (
    None
):
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
        split_boundaries={
            "train": ("2026-01-01T00:00:00+00:00", "2026-01-07T00:00:00+00:00")
        },
        adequacy_floor=20,
        ablation_comparison_plan="compare baseline and drift-aware variants",
    )
    recorded_hash = compute_predeclaration_hash(artifact)
    assert (
        validate_predeclaration_artifact(artifact, expected_hash=recorded_hash) is True
    )
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
        split_boundaries={
            "train": ("2026-01-01T00:00:00+00:00", "2026-01-07T00:00:00+00:00")
        },
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
        split_boundaries={
            "train": ("2026-01-01T00:00:00+00:00", "2026-01-07T00:00:00+00:00")
        },
        adequacy_floor=20,
        ablation_comparison_plan="compare baseline and drift-aware variants",
    )
    with pytest.raises(ValueError):
        validate_predeclaration_artifact(window_derived)


def test_predeclaration_provenance_requires_anchor_and_ancestry(tmp_path) -> None:
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
        split_boundaries={
            "train": ("2026-01-01T00:00:00+00:00", "2026-01-07T00:00:00+00:00")
        },
        adequacy_floor=20,
        ablation_comparison_plan="compare baseline and drift-aware variants",
    )
    recorded_hash = compute_predeclaration_hash(artifact)

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=tmp_path, check=True, text=True, capture_output=True
        ).stdout.strip()

    git("init")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Isoprax Test")
    (tmp_path / "plan.txt").write_text("frozen", encoding="utf-8")
    git("add", "plan.txt")
    git("commit", "-m", "predeclaration")
    predeclaration_commit = git("rev-parse", "HEAD")
    (tmp_path / "corpus.txt").write_text("later", encoding="utf-8")
    git("add", "corpus.txt")
    git("commit", "-m", "corpus data")
    corpus_commit = git("rev-parse", "HEAD")

    provenance = evaluate_predeclaration_provenance(
        artifact,
        artifact_hash=recorded_hash,
        predeclaration_commit=predeclaration_commit,
        corpus_data_commits=(corpus_commit,),
        external_anchor={
            "anchor_type": "remote_push",
            "anchor_reference": "https://example.com/repo",
            "independent_of_repository_and_clock": True,
        },
        remote_configured=True,
        repository_pushed=True,
        repository_path=tmp_path,
        commit_timestamps={
            predeclaration_commit: "2026-01-02T00:00:00+00:00",
            corpus_commit: "2026-01-03T00:00:00+00:00",
        },
    )
    assert provenance.anchored is True
    assert provenance.ancestry_ok is True

    with pytest.raises(ValueError, match="external anchor"):
        evaluate_predeclaration_provenance(
            artifact,
            artifact_hash=recorded_hash,
            predeclaration_commit=predeclaration_commit,
            corpus_data_commits=(corpus_commit,),
            repository_path=tmp_path,
        )

    with pytest.raises(ValueError):
        evaluate_predeclaration_provenance(
            artifact,
            artifact_hash=recorded_hash,
            predeclaration_commit=predeclaration_commit,
            corpus_data_commits=(corpus_commit,),
            external_anchor={
                "anchor_type": "remote_push",
                "anchor_reference": "https://example.com/repo",
                "independent_of_repository_and_clock": True,
            },
            remote_configured=True,
            repository_pushed=True,
            repository_path=tmp_path,
            commit_timestamps={
                predeclaration_commit: "2026-01-10T00:00:00+00:00",
                corpus_commit: "2026-01-05T00:00:00+00:00",
            },
        )


def test_screening_derives_frozen_floor_and_requires_all_sampled_allowlist_fields() -> (
    None
):
    rates = [0.99] * 190 + [0.876] * 10
    assert derive_build_floor(rates, reference_project_id="unrelated") == 0.87
    candidate = {
        "system_id": "candidate",
        "commit_supply": 200,
        "observed_positive_rate": 0.2,
        "licence_forbids_publication": False,
        "licence_forbids_redistribution": False,
        "sampled_build_success_rate": 0.88,
        "build_attempts": 20,
        "build_failures_clustered": False,
        "sampled_prediction_fields": {
            "commit-a": {"allowed": 1},
            "commit-b": {"forbidden": 2},
        },
    }
    record = screen_candidates(
        [candidate],
        adequacy_floor=20,
        reference_build_success_rates=rates,
        reference_project_id="unrelated",
        prediction_time_feature_allowlist={"allowed"},
    )[0]
    assert record.disqualifying_screen == "prediction_metadata"

    clustered = {
        **candidate,
        "sampled_prediction_fields": {"commit-a": {"allowed": 1}},
        "build_failures_clustered": True,
    }
    assert (
        screen_candidates(
            [clustered],
            adequacy_floor=20,
            reference_build_success_rates=[0.99] * 200,
            reference_project_id="unrelated",
            prediction_time_feature_allowlist={"allowed"},
        )[0].disqualifying_screen
        == "build_rate"
    )
    assert derive_build_floor([0.99] * 200, reference_project_id="unrelated") == 0.90

    with pytest.raises(ValueError, match="exactly 200"):
        derive_build_floor([0.99], reference_project_id="unrelated")


def test_exclusion_entries_stay_structural_not_pending() -> None:
    no_change = record_exclusion_entry(
        "dataset-no-change",
        exclusion_type="structural_no_change_events",
        reason="This dataset is structurally excluded because no Change-family event exists to condition on; it remains available only as a baseline reference.",
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

    replay_justification = build_replay_justification_exclusion(
        "dataset-shared-process"
    )
    assert replay_justification.cited_spec == "Isoprax v0.3 §5.6"
    assert "paired dataset" in replay_justification.reason.lower()


def test_early_screen_requires_governing_terms_and_hermeticity_without_build_rate() -> (
    None
):
    base = {
        "system_id": "early-candidate",
        "estimated_buildable_window_commits": 200,
        "observed_positive_rate": 0.2,
        "sampled_prediction_fields": {"commit-a": {"allowed": 1}},
        "sampled_build_success_rate": 0.0,
        "legal_instruments": [
            {
                "instrument_type": "license",
                "reference": "LICENSE",
                "governs_source_built_artifact": True,
                "forbids_publication": False,
                "forbids_redistribution": False,
            }
        ],
        "replay_readiness_evidence": {
            "hermeticity_class": "pinned_container_toolchain",
            "evidence_reference": "Containerfile.lock",
        },
    }
    eligible = screen_early_candidate(
        base, adequacy_floor=20, prediction_time_feature_allowlist={"allowed"}
    )
    assert eligible.eligible is True
    assert len(eligible.screen_results) == 4
    assert (
        eligible.metadata["historical_build_rate_qualification"]
        == "deferred_to_replay_environment"
    )

    missing_terms = screen_early_candidate(
        {**base, "legal_instruments": []},
        adequacy_floor=20,
        prediction_time_feature_allowlist={"allowed"},
    )
    assert missing_terms.disqualifying_screen == "governing_legal_terms"
    assert len(missing_terms.screen_results) == 2

    restricted = screen_early_candidate(
        {
            **base,
            "legal_instruments": [
                {
                    **base["legal_instruments"][0],
                    "forbids_publication": True,
                }
            ],
        },
        adequacy_floor=20,
        prediction_time_feature_allowlist={"allowed"},
    )
    assert restricted.disqualifying_screen == "governing_legal_terms"
    assert restricted.metadata["governing_legal_instrument"]["reference"] == "LICENSE"

    conventional = screen_early_candidate(
        {
            **base,
            "replay_readiness_evidence": {
                "hermeticity_class": "conventional",
                "evidence_reference": "README.md",
            },
        },
        adequacy_floor=20,
        prediction_time_feature_allowlist={"allowed"},
    )
    assert conventional.disqualifying_screen == "replay_readiness"
    assert len(conventional.screen_results) == 3
