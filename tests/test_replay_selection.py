from __future__ import annotations

import subprocess
from dataclasses import replace

import pytest
from hypothesis import given
from hypothesis import strategies as st

import isoprax.replay_selection as replay
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


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=12),
        st.integers(),
        min_size=1,
        max_size=12,
    )
)
def test_predeclaration_hash_is_invariant_to_mapping_insertion_order(payload):
    reordered = dict(reversed(list(payload.items())))

    assert replay.hash_predeclaration_artifact(
        payload
    ) == replay.hash_predeclaration_artifact(reordered)


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


def test_screening_guards_cover_malformed_boundary_evidence() -> None:
    assert replay._screen_commit_supply({})[0] is False
    assert replay._screen_commit_supply({"commit_supply": "bad"})[0] is False
    assert (
        replay._screen_commit_supply(
            {"commit_supply": 100, "observed_positive_rate": "bad"}, adequacy_floor=1
        )[0]
        is False
    )
    assert (
        replay._screen_commit_supply(
            {"commit_supply": 100, "estimated_positive_event_rate": 0.2},
            adequacy_floor=20,
        )[0]
        is True
    )
    assert replay._screen_build_rate({}, build_floor=0.9)[0] is False
    assert (
        replay._screen_build_rate(
            {"sampled_build_success_rate": "bad"}, build_floor=0.9
        )[0]
        is False
    )
    assert (
        replay._screen_build_rate(
            {"sampled_build_success_rate": 0.9, "build_attempts": "bad"},
            build_floor=0.9,
        )[0]
        is False
    )
    assert (
        replay._screen_build_rate(
            {
                "sampled_build_success_rate": 0.9,
                "build_attempts": 1,
                "build_failures_clustered": True,
            },
            build_floor=0.9,
        )[0]
        is False
    )
    assert (
        replay._screen_prediction_metadata(
            {}, prediction_time_feature_allowlist=frozenset({"ok"})
        )[0]
        is False
    )
    assert (
        replay._screen_prediction_metadata(
            {"sampled_prediction_fields": {"": {"ok": 1}}},
            prediction_time_feature_allowlist=frozenset({"ok"}),
        )[0]
        is False
    )
    assert (
        replay._screen_prediction_metadata(
            {"sampled_prediction_fields": {"c": {"ok": 1}}},
            prediction_time_feature_allowlist=frozenset(),
        )[0]
        is False
    )
    assert replay._screen_estimated_buildable_window({}, adequacy_floor=1)[0] is False
    assert (
        replay._screen_estimated_buildable_window(
            {"estimated_buildable_window_commits": 2, "observed_positive_rate": 0.1},
            adequacy_floor=1,
        )[0]
        is False
    )
    assert (
        replay._screen_governing_legal_terms({"legal_instruments": "LICENSE"})[0]
        is False
    )
    assert (
        replay._screen_governing_legal_terms(
            {"legal_instruments": [{"governs_source_built_artifact": True}]}
        )[0]
        is False
    )
    assert (
        replay._screen_replay_readiness({"replay_readiness_evidence": []})[0] is False
    )
    assert (
        replay._screen_replay_readiness(
            {"replay_readiness_evidence": {"hermeticity_class": "hermetic_build"}}
        )[0]
        is False
    )


def test_replay_utility_errors_and_compatibility_aliases() -> None:
    with pytest.raises(TypeError):
        replay._coerce_mapping(object())
    assert replay._as_bool("allowed") is True
    assert replay._as_bool(None, default=True) is True
    with pytest.raises(ValueError, match="system_id"):
        replay.CandidateRecord("", True, None)
    with pytest.raises(ValueError, match="reference_project_id"):
        derive_build_floor([0.9] * 200, reference_project_id=" ")
    with pytest.raises(ValueError, match="numeric"):
        derive_build_floor(["bad"] * 200, reference_project_id="other")
    with pytest.raises(ValueError, match="within"):
        derive_build_floor([2] * 200, reference_project_id="other")
    candidate = {
        "system_id": "candidate",
        "commit_supply": 200,
        "observed_positive_rate": 0.2,
        "sampled_build_success_rate": 1,
        "build_attempts": 1,
        "sampled_prediction_fields": {"c": {"ok": 1}},
    }
    with pytest.raises(ValueError, match="unrelated"):
        replay.screen_candidate(
            candidate,
            adequacy_floor=1,
            reference_build_success_rates=[1] * 200,
            reference_project_id="candidate",
            prediction_time_feature_allowlist={"ok"},
        )
    with pytest.deprecated_call():
        assert replay.evaluate_candidate_screening(
            [candidate],
            adequacy_floor=1,
            reference_build_success_rates=[1] * 200,
            reference_project_id="other",
            prediction_time_feature_allowlist={"ok"},
        )
    with pytest.deprecated_call():
        assert replay.screen_candidate_system(
            candidate,
            adequacy_floor=1,
            reference_build_success_rates=[1] * 200,
            reference_project_id="other",
            prediction_time_feature_allowlist={"ok"},
        ).eligible


def test_predeclaration_mapping_and_provenance_fail_closed() -> None:
    raw = {
        "artifact_id": "map",
        "content": "frozen",
        "soak_duration": "7d",
        "soak_duration_rule": "training-only",
        "positive_event_definition": "observed",
        "positive_event_thresholds": {"minimum": 1},
        "censoring_rule": "drop",
        "drift_threshold": 0.1,
        "anchor_threshold": 0.1,
        "split_boundaries": {"train": {"start": "a", "end": "b"}},
        "adequacy_floor": 1,
        "ablation_comparison_plan": "compare",
    }
    assert validate_predeclaration_artifact(raw)
    assert replay.hash_predeclaration_artifact(
        raw
    ) == replay.hash_predeclaration_artifact(dict(reversed(list(raw.items()))))
    with pytest.raises(ValueError, match="exactly two"):
        validate_predeclaration_artifact({**raw, "split_boundaries": {"train": ["a"]}})
    with pytest.raises(ValueError, match="sequence or mapping"):
        validate_predeclaration_artifact({**raw, "split_boundaries": {"train": 1}})
    with pytest.raises(ValueError, match="observation window"):
        validate_predeclaration_artifact(
            {**raw, "soak_duration_rule": "observation derived"},
            observation_window="test",
        )
    with pytest.raises(ValueError, match="predeclaration_commit"):
        evaluate_predeclaration_provenance(
            raw,
            external_anchor={
                "type": "x",
                "reference": "r",
                "independent_of_repository_and_clock": True,
            },
        )
    with pytest.raises(ValueError, match="independent"):
        evaluate_predeclaration_provenance(
            raw,
            predeclaration_commit="p",
            external_anchor={"type": "x", "reference": "r"},
        )
    with pytest.raises(ValueError, match="remote push"):
        evaluate_predeclaration_provenance(
            raw,
            predeclaration_commit="p",
            external_anchor={
                "type": "remote_push",
                "reference": "r",
                "independent_of_repository_and_clock": True,
            },
        )
    with pytest.raises(ValueError, match="ancestor"):
        evaluate_predeclaration_provenance(
            raw,
            predeclaration_commit="p",
            corpus_data_commits=("c",),
            external_anchor={
                "type": "x",
                "reference": "r",
                "independent_of_repository_and_clock": True,
            },
            repository_path=".",
            git_runner=lambda _command, _path: False,
        )
    assert replay._ancestor_check("p", (), repository_path=None) is True
    assert replay._ancestor_check("", ("c",), repository_path=".") is False
    with pytest.raises(ValueError, match="repository_path"):
        replay._ancestor_check("p", ("c",), repository_path=None)
    assert replay._infer_commit_time("p", timestamps={"p": "bad"}) is None


def test_exclusion_validation_and_later_dataset_justification() -> None:
    with pytest.raises(ValueError, match="dataset_id"):
        replay.ExclusionEntry(
            "", "structural_no_change_events", replay._NO_CHANGE_EVENT_SENTINEL
        )
    with pytest.raises(ValueError, match="unsupported"):
        record_exclusion_entry("x", exclusion_type="unknown", reason="reason")
    with pytest.raises(ValueError, match="pending"):
        record_exclusion_entry(
            "x",
            exclusion_type="structural_no_change_events",
            reason=replay._NO_CHANGE_EVENT_SENTINEL,
            pending=True,
        )
    assert (
        "later paired"
        in build_replay_justification_exclusion(
            "x", paired_dataset_available=True
        ).reason.lower()
    )


def test_predeclaration_value_objects_reject_each_missing_required_field() -> None:
    artifact = PredeclarationArtifact(
        artifact_id="id",
        content="content",
        soak_duration="7d",
        soak_duration_rule="training-only",
        positive_event_definition="observed",
        positive_event_thresholds={"x": 1},
        censoring_rule="drop",
        drift_threshold=0.1,
        anchor_threshold=0.1,
        split_boundaries={"train": ("a", "b")},
        adequacy_floor=1,
        ablation_comparison_plan="compare",
    )
    for field, value in (
        ("artifact_id", ""),
        ("content", ""),
        ("soak_duration", ""),
        ("soak_duration_rule", ""),
        ("positive_event_definition", ""),
        ("positive_event_thresholds", {}),
        ("censoring_rule", ""),
        ("split_boundaries", {}),
        ("adequacy_floor", -1),
        ("ablation_comparison_plan", ""),
    ):
        with pytest.raises(ValueError):
            replace(artifact, **{field: value})
    assert artifact.to_dict()["split_boundaries"]["train"] == ["a", "b"]
    mapping = artifact.to_dict()
    mapping["split_boundaries"] = {"train": ["a", "b"]}
    assert validate_predeclaration_artifact(mapping)


def test_provenance_timestamp_and_exclusion_failures_are_not_silenced() -> None:
    artifact = PredeclarationArtifact(
        artifact_id="id",
        content="content",
        soak_duration="7d",
        soak_duration_rule="training-only",
        positive_event_definition="observed",
        positive_event_thresholds={"x": 1},
        censoring_rule="drop",
        drift_threshold=0.1,
        anchor_threshold=0.1,
        split_boundaries={"train": ("a", "b")},
        adequacy_floor=1,
        ablation_comparison_plan="compare",
    )
    anchor = {
        "type": "x",
        "reference": "r",
        "independent_of_repository_and_clock": True,
    }
    with pytest.raises(ValueError, match="hash mismatch"):
        evaluate_predeclaration_provenance(
            artifact,
            artifact_hash="expected",
            observed_hash="observed",
            predeclaration_commit="p",
            external_anchor=anchor,
        )
    with pytest.raises(ValueError, match="predates"):
        evaluate_predeclaration_provenance(
            artifact,
            predeclaration_commit="p",
            corpus_data_commits=("c",),
            external_anchor=anchor,
            repository_path=".",
            git_runner=lambda _command, _path: True,
            commit_timestamps={
                "p": "2026-02-01T00:00:00+00:00",
                "c": "2026-01-01T00:00:00+00:00",
            },
        )
    for exclusion_type in (
        "structural_no_change_events",
        "commensurability_mismatch",
        "structural_replay_justification",
    ):
        with pytest.raises(ValueError):
            record_exclusion_entry("x", exclusion_type=exclusion_type, reason="wrong")
