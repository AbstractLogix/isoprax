from dataclasses import replace

import pytest

from isoprax.commensurability import Attestation, OutcomeDefinition
from isoprax.replay_capture import (
    DeploymentEvidence,
    ObservationArtifactEvidence,
    ObservationEvidence,
    ReplayCaptureRecord,
    ReplayLaneDefinition,
)
from isoprax.stage2_feasibility import (
    CLAIM_BOUNDARY,
    BootstrapYieldEstimate,
    FeasibilityGate,
    RepeatabilityCheck,
    ReplayPilotProfile,
    ReplayTerminalRecord,
    build_stage2_feasibility_report,
    compare_repeatability,
    estimate_stage2_yield,
    normalize_replay_records,
    validate_stage2_feasibility_report,
)


def test_all_negative_yield_is_explicitly_non_estimable():
    estimate = estimate_stage2_yield(
        ["observed_negative"] * 3,
        target_positive=2,
        target_negative=2,
        bootstrap_samples=200,
        seed=7,
    )

    assert isinstance(estimate, BootstrapYieldEstimate)
    assert estimate.status == "no_positive_events"
    assert estimate.implied_records_point is None
    assert estimate.implied_records_conservative is None
    assert estimate.to_dict()["counts"] == {
        "selected": 3,
        "labeled": 3,
        "positive": 0,
        "negative": 3,
        "censored": 0,
        "blocked": 0,
    }


def test_bootstrap_yield_is_deterministic_and_reports_planning_size():
    outcome_classes = (
        "observed_positive",
        "observed_negative",
        "observed_negative",
        "observed_positive",
        "censored",
    )
    first = estimate_stage2_yield(
        outcome_classes,
        target_positive=2,
        target_negative=2,
        bootstrap_samples=200,
        seed=11,
    )
    second = estimate_stage2_yield(
        outcome_classes,
        target_positive=2,
        target_negative=2,
        bootstrap_samples=200,
        seed=11,
    )

    assert first == second
    assert first.status == "estimable"
    assert first.implied_records_point is not None
    assert first.implied_records_conservative is None or (
        first.implied_records_conservative >= first.implied_records_point
    )
    assert 0 <= first.positive_ci_low <= first.positive_ci_high <= 1
    assert 0 <= first.negative_ci_low <= first.negative_ci_high <= 1


@pytest.mark.parametrize(
    "outcome_classes, target_positive, target_negative, bootstrap_samples, message",
    [
        (("observed_positive",), 0, 1, 200, "targets"),
        (("observed_positive",), 1, 1, 99, "bootstrap_samples"),
        ((), 1, 1, 200, "outcome classes"),
        (("unknown",), 1, 1, 200, "unknown outcome classes"),
    ],
)
def test_yield_estimate_rejects_invalid_inputs(
    outcome_classes, target_positive, target_negative, bootstrap_samples, message
):
    with pytest.raises(ValueError, match=message):
        estimate_stage2_yield(
            outcome_classes,
            target_positive=target_positive,
            target_negative=target_negative,
            bootstrap_samples=bootstrap_samples,
        )


def definition(identifier: str, *, window: str = "10m") -> OutcomeDefinition:
    return OutcomeDefinition(
        identifier,
        "threshold breach",
        {"kind": "shared_telemetry", "parameters": {"metric": "error_rate"}},
        {"duration": 10, "unit": "minute", "anchor": "score_time", "raw": window},
        ({"metric": "error_rate", "operator": ">", "value": 0.2},),
    )


def profile(
    commits=("change-a", "change-b"),
    *,
    change=None,
    operational=None,
    attestation=None,
    require_repeatability=False,
):
    return ReplayPilotProfile(
        "candidate-a",
        "system-a",
        "service-a",
        tuple(commits),
        "workload-v1",
        change or definition("change-definition"),
        operational or definition("operational-definition"),
        "PT10M",
        "threshold-v1",
        "schema-v1",
        "public-replay",
        ("manifest.json",),
        "predeclaration-hash",
        "anchor://predeclaration",
        "predeclaration-commit",
        ("corpus-commit",),
        True,
        frozenset({"diff_size"}),
        frozenset({"future_metric"}),
        1,
        True,
        1.0,
        require_repeatability,
        attestation,
    )


def capture(
    commit="change-a",
    outcome_class="observed_positive",
    *,
    private=False,
    deployment=True,
    reason=None,
    lane_changes=None,
):
    lane_values = {
        "system_id": "system-a",
        "service_id": "service-a",
        "commit": commit,
        "workload_reference": "workload-v1",
        "horizon_rule": "PT10M",
        "outcome_threshold_rule": "threshold-v1",
        "capture_schema_version": "schema-v1",
        "allowed_evidence_scope": "public-replay",
        "score_time": "2026-09-02T00:00:00Z",
        "window_start": "2026-09-02T00:00:00Z",
        "window_end": "2026-09-02T00:10:00Z",
    }
    lane_values.update(lane_changes or {})
    lane = ReplayLaneDefinition(**lane_values)
    deployment_evidence = (
        DeploymentEvidence(
            "target-a",
            commit,
            "succeeded",
            "2026-09-02T00:00:01Z",
            "2026-09-02T00:00:02Z",
            "deployment-a",
        )
        if deployment
        else None
    )
    observation = (
        ObservationEvidence(
            lane.score_time,
            lane.window_start,
            lane.window_end,
            True,
            True,
            True,
            outcome_class == "observed_positive",
            private,
            False,
            lane.allowed_evidence_scope,
            ("metrics.json",),
            {"metrics.json": b"secret-payload"},
            "observed",
        )
        if outcome_class.startswith("observed")
        else None
    )
    artifacts = (
        (ObservationArtifactEvidence("metrics.json", "collected", "abc", 3),)
        if observation
        else ()
    )
    return ReplayCaptureRecord(
        f"lane-{commit}",
        lane,
        "qualification-hash",
        "execution-hash",
        deployment_evidence,
        observation,
        artifacts,
        outcome_class,
        reason,
    )


def records_for(pilot, *, run="run-1", private=False):
    return normalize_replay_records(
        pilot,
        [
            capture("change-a", private=private),
            capture("change-b", "observed_negative"),
        ],
        run_identity=run,
        prediction_fields={
            "change-a": {"diff_size": "2026-09-01T23:59:00Z"},
            "change-b": {"diff_size": "2026-09-01T23:59:00Z"},
        },
    )


def test_profile_identity_and_direct_commensurability_are_deterministic():
    first = profile()
    second = profile()
    assert first.profile_identity == second.profile_identity
    assert first.commensurability().level == "direct"


def test_profile_rejects_invalid_ordering_and_irreducible_definitions():
    with pytest.raises(ValueError, match="ancestor"):
        profile().__class__(
            **{**profile().__dict__, "predeclaration_is_ancestor": False}
        )
    with pytest.raises(ValueError, match="shared outcome"):
        profile(
            operational=OutcomeDefinition(
                "other",
                "threshold breach",
                {"kind": "different"},
                {"duration": 10, "unit": "minute", "anchor": "score_time"},
            )
        )


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"candidate_id": ""}, "metadata"),
        ({"selected_commits": ()}, "selected commits"),
        ({"selected_commits": ("change-a", "change-a")}, "unique"),
        ({"published_artifacts": ()}, "published artifacts"),
        ({"corpus_data_commits": ("same", "same")}, "corpus data"),
        ({"min_complete_records": 0}, "min_complete"),
        ({"min_observation_rate": 2}, "between 0 and 1"),
        ({"change_definition": "invalid"}, "outcome definitions"),
    ],
)
def test_profile_rejects_malformed_declarations(changes, message):
    with pytest.raises(ValueError, match=message):
        ReplayPilotProfile(**{**profile().__dict__, **changes})


def test_profile_rejects_non_string_metadata_and_terminal_labels_need_shared_lineage():
    with pytest.raises(ValueError, match="metadata"):
        ReplayPilotProfile(**{**profile().__dict__, "candidate_id": None})
    with pytest.raises(ValueError, match="shared family labels"):
        ReplayTerminalRecord(
            "change-a",
            "lane",
            "run",
            "observed_positive",
            "observation",
            None,
            capture("change-a"),
        )


def test_attested_equivalence_is_preserved():
    left = definition("left")
    right = OutcomeDefinition(
        "right",
        left.event,
        left.observation_process,
        {"duration": 20, "unit": "minute", "anchor": "score_time"},
        left.thresholds,
    )
    attestation = Attestation(
        "reviewer", "same event after retained replay", "left", "right", "evidence://1"
    )
    pilot = profile(change=left, operational=right, attestation=attestation)
    assert pilot.commensurability().level == "attested"


def test_bridgeable_definition_is_not_accepted_for_shared_label_pilot():
    left = definition("left")
    right = OutcomeDefinition(
        "right",
        left.event,
        left.observation_process,
        {"duration": 20, "unit": "minute", "anchor": "score_time"},
        left.thresholds,
    )
    with pytest.raises(ValueError, match="shared outcome"):
        profile(change=left, operational=right)


def test_normalization_preserves_complete_and_censored_terminal_records():
    pilot = profile()
    records = normalize_replay_records(
        pilot,
        [
            capture("change-a"),
            capture(
                "change-b",
                "censored",
                deployment=False,
                reason="build qualification failed",
            ),
        ],
        run_identity="run-1",
        prediction_fields={
            "change-a": {"diff_size": "2026-09-01T23:59:00Z"},
            "change-b": {"diff_size": "2026-09-01T23:59:00Z"},
        },
    )
    assert records[0].terminal_status == "observed_positive"
    assert records[1].terminal_status == "blocked-before-compilation"
    assert records[1].reason == "build qualification failed"


def test_normalization_rejects_missing_duplicate_and_lane_mismatch():
    pilot = profile()
    with pytest.raises(ValueError, match="lack terminal"):
        normalize_replay_records(
            pilot,
            [capture("change-a")],
            run_identity="run-1",
            prediction_fields={"change-a": {"diff_size": "2026-09-01T23:59:00Z"}},
        )
    with pytest.raises(ValueError, match="multiple"):
        normalize_replay_records(
            pilot,
            [capture("change-a"), capture("change-a")],
            run_identity="run-1",
            prediction_fields={"change-a": {"diff_size": "2026-09-01T23:59:00Z"}},
        )


def test_normalization_rejects_empty_run_invalid_capture_and_outside_sample():
    pilot = profile()
    with pytest.raises(ValueError, match="run_identity"):
        normalize_replay_records(pilot, [], run_identity=" ")
    with pytest.raises(ValueError, match="capture record"):
        normalize_replay_records(pilot, [object()], run_identity="run-1")
    with pytest.raises(ValueError, match="outside"):
        normalize_replay_records(
            pilot,
            [capture("other")],
            run_identity="run-1",
        )


def test_terminal_and_gate_contracts_reject_invalid_values():
    pilot = profile()
    valid_capture = capture("change-a")
    with pytest.raises(ValueError, match="identity"):
        ReplayTerminalRecord(
            "", "lane", "run", "observed_positive", "observation", None, valid_capture
        )
    with pytest.raises(ValueError, match="status"):
        ReplayTerminalRecord(
            "a", "lane", "run", "unknown", "observation", None, valid_capture
        )
    with pytest.raises(ValueError, match="reason"):
        ReplayTerminalRecord(
            "a", "lane", "run", "censored", "observation", None, valid_capture
        )
    with pytest.raises(ValueError, match="capture"):
        ReplayTerminalRecord(
            "a", "lane", "run", "observed_positive", "observation", None, object()
        )
    with pytest.raises(ValueError, match="status"):
        RepeatabilityCheck("lane", (), True, True, True, (), "unknown")
    with pytest.raises(ValueError, match="status"):
        FeasibilityGate("gate", "unknown", "bad")
    with pytest.raises(ValueError, match="frozen"):
        normalize_replay_records(
            pilot,
            [
                capture("change-a"),
                capture("change-b", lane_changes={"service_id": "other"}),
            ],
            run_identity="run-1",
            prediction_fields={
                "change-a": {"diff_size": "2026-09-01T23:59:00Z"},
                "change-b": {"diff_size": "2026-09-01T23:59:00Z"},
            },
        )


def test_prediction_time_boundary_and_field_allowlist_are_enforced():
    pilot = profile()
    with pytest.raises(ValueError, match="missing"):
        normalize_replay_records(
            pilot, [capture("change-a"), capture("change-b")], run_identity="run"
        )
    with pytest.raises(ValueError, match="post-score"):
        normalize_replay_records(
            pilot,
            [capture("change-a"), capture("change-b")],
            run_identity="run",
            prediction_fields={
                "change-a": {"diff_size": "2026-09-02T00:00:01Z"},
                "change-b": {"diff_size": "2026-09-01T23:59:00Z"},
            },
        )
    with pytest.raises(ValueError, match="not allowed"):
        normalize_replay_records(
            pilot,
            [capture("change-a"), capture("change-b")],
            run_identity="run",
            prediction_fields={
                "change-a": {"unknown": "2026-09-01T23:59:00Z"},
                "change-b": {"diff_size": "2026-09-01T23:59:00Z"},
            },
        )
    with pytest.raises(ValueError, match="forbidden"):
        forbidden = replace(
            pilot,
            allowed_prediction_fields=frozenset({"diff_size", "future_metric"}),
        )
        normalize_replay_records(
            forbidden,
            [capture("change-a"), capture("change-b")],
            run_identity="run",
            prediction_fields={
                "change-a": {"future_metric": "2026-09-01T23:59:00Z"},
                "change-b": {"future_metric": "2026-09-01T23:59:00Z"},
            },
        )
    with pytest.raises(ValueError, match="invalid"):
        normalize_replay_records(
            pilot,
            [capture("change-a"), capture("change-b")],
            run_identity="run",
            prediction_fields={
                "change-a": object(),
                "change-b": {"diff_size": "2026-09-01T23:59:00Z"},
            },
        )
    with pytest.raises(ValueError, match="timestamp"):
        normalize_replay_records(
            pilot,
            [capture("change-a"), capture("change-b")],
            run_identity="run",
            prediction_fields={
                "change-a": {"diff_size": "not-a-timestamp"},
                "change-b": {"diff_size": "2026-09-01T23:59:00Z"},
            },
        )


def test_feasible_report_is_deterministic_and_validatable_without_payloads():
    pilot = profile()
    records = records_for(pilot)
    report = build_stage2_feasibility_report(
        pilot,
        records,
        throughput={"build": 3, "observation": 5},
        extrapolation={"assumption": "linear pilot rate", "uncertainty": "declared"},
    )
    second = build_stage2_feasibility_report(pilot, records)
    validate_stage2_feasibility_report(report)
    assert report.status == "feasible"
    assert report.report_identity != second.report_identity
    assert report.counts["selected"] == 2
    assert report.counts["complete_observations"] == 2
    assert "secret-payload" not in str(report.to_dict())
    assert "Semantic" in CLAIM_BOUNDARY


def test_report_is_inconclusive_when_outcome_class_or_rate_is_missing():
    pilot = profile(("change-a",), require_repeatability=False)
    records = normalize_replay_records(
        pilot,
        [capture("change-a")],
        run_identity="run-1",
        prediction_fields={"change-a": {"diff_size": "2026-09-01T23:59:00Z"}},
    )
    report = build_stage2_feasibility_report(pilot, records)
    assert report.status == "inconclusive"
    assert any(gate.gate_id == "outcome_diversity" for gate in report.gates)


def test_report_labels_optional_outcome_diversity_without_overclaiming():
    pilot = profile(("change-a",), require_repeatability=False)
    pilot = replace(pilot, require_both_outcomes=False)
    records = normalize_replay_records(
        pilot,
        [capture("change-a")],
        run_identity="run-1",
        prediction_fields={"change-a": {"diff_size": "2026-09-01T23:59:00Z"}},
    )
    report = build_stage2_feasibility_report(pilot, records)
    gate = next(gate for gate in report.gates if gate.gate_id == "outcome_diversity")
    assert gate.status == "pass"
    assert gate.message == "outcome diversity is not required by this pilot"


def test_private_observation_blocks_release():
    pilot = profile()
    report = build_stage2_feasibility_report(pilot, records_for(pilot, private=True))
    assert report.status == "blocked"
    assert report.counts["release_withheld"] == 1


def test_repeatability_preserves_disagreement_and_required_repeatability():
    pilot = profile(require_repeatability=True)
    first = records_for(pilot, run="run-1")
    second = records_for(pilot, run="run-2")
    differing = tuple(
        replace(record, terminal_status="censored", reason="repeat mismatch")
        if record.commit == "change-b"
        else record
        for record in second
    )
    checks = compare_repeatability((first, differing))
    assert any("terminal status differs" in item.discrepancies for item in checks)
    report = build_stage2_feasibility_report(pilot, first, repeatability=checks)
    assert report.status == "inconclusive"


def test_repeatability_detects_missing_labels_and_artifacts():
    pilot = profile()
    first = records_for(pilot, run="run-1")
    changed = tuple(
        replace(
            record,
            capture=replace(record.capture, outcome_class="observed_negative")
            if record.commit == "change-a"
            else record.capture,
            artifact_manifest=({"path": "different.json", "state": "collected"},)
            if record.commit == "change-b"
            else record.artifact_manifest,
        )
        for record in first
    )
    checks = compare_repeatability((first, changed, (first[0],)))
    assert any("missing terminal record" in item.discrepancies for item in checks)
    assert any("outcome label differs" in item.discrepancies for item in checks)
    assert any("artifact manifest differs" in item.discrepancies for item in checks)
    assert compare_repeatability(()) == ()


def test_repeatability_detects_family_label_disagreement():
    pilot = profile()
    first = records_for(pilot, run="run-1")
    second = tuple(
        replace(record, change_label="different", operational_label="different")
        if record.commit == "change-a"
        else record
        for record in first
    )
    checks = compare_repeatability((first, second))
    assert any("family labels differ" in item.discrepancies for item in checks)


def test_normalization_rejects_lineage_and_artifact_gaps_and_keeps_generic_censoring():
    pilot = profile()
    prediction_fields = {
        "change-a": {"diff_size": "2026-09-01T23:59:00Z"},
        "change-b": {"diff_size": "2026-09-01T23:59:00Z"},
    }
    with pytest.raises(ValueError, match="qualification"):
        normalize_replay_records(
            pilot,
            [
                replace(capture("change-a"), qualification_report_hash=""),
                capture("change-b"),
            ],
            run_identity="run",
            prediction_fields=prediction_fields,
        )
    with pytest.raises(ValueError, match="deployment"):
        normalize_replay_records(
            pilot,
            [
                replace(
                    capture("change-a"),
                    deployment=replace(
                        capture("change-a").deployment, evidence_reference=""
                    ),
                ),
                capture("change-b"),
            ],
            run_identity="run",
            prediction_fields=prediction_fields,
        )
    with pytest.raises(ValueError, match="artifact"):
        normalize_replay_records(
            pilot,
            [
                replace(
                    capture("change-a"),
                    artifacts=(
                        ObservationArtifactEvidence("metrics.json", "collected"),
                    ),
                ),
                capture("change-b"),
            ],
            run_identity="run",
            prediction_fields=prediction_fields,
        )
    records = normalize_replay_records(
        pilot,
        [capture("change-a", "censored", reason="monitoring gap"), capture("change-b")],
        run_identity="run",
        prediction_fields=prediction_fields,
    )
    assert records[0].terminal_status == "censored"


def test_required_repeatability_without_second_run_is_inconclusive():
    pilot = profile(require_repeatability=True)
    report = build_stage2_feasibility_report(pilot, records_for(pilot))
    assert report.status == "inconclusive"


def test_report_validator_rejects_tampered_identity_and_counts():
    pilot = profile()
    report = build_stage2_feasibility_report(pilot, records_for(pilot))
    with pytest.raises(ValueError, match="identity"):
        validate_stage2_feasibility_report(replace(report, report_identity="tampered"))
    with pytest.raises(ValueError, match="complete count"):
        validate_stage2_feasibility_report(
            replace(report, counts={**report.counts, "complete_observations": 1})
        )


def test_report_builder_and_validator_reject_invalid_records_and_reports():
    pilot = profile()
    records = records_for(pilot)
    with pytest.raises(ValueError, match="unique commits"):
        build_stage2_feasibility_report(pilot, records + (records[0],))
    with pytest.raises(ValueError, match="cover"):
        build_stage2_feasibility_report(pilot, records[:1])
    report = build_stage2_feasibility_report(pilot, records)
    with pytest.raises(ValueError, match="invalid"):
        validate_stage2_feasibility_report(object())
    with pytest.raises(ValueError, match="summaries"):
        validate_stage2_feasibility_report(replace(report, terminal_summaries=()))
    with pytest.raises(ValueError, match="exceeds"):
        validate_stage2_feasibility_report(
            replace(report, counts={**report.counts, "selected": 1})
        )
    with pytest.raises(ValueError, match="terminal classes"):
        validate_stage2_feasibility_report(
            replace(
                report,
                counts={
                    **report.counts,
                    "observed_positive": report.counts["observed_positive"] + 1,
                    "complete_observations": report.counts["complete_observations"] + 1,
                },
            )
        )
    with pytest.raises(ValueError, match="status"):
        replace(report, status="unknown")
    with pytest.raises(ValueError, match="claim boundary"):
        replace(report, claim_boundary="semantic")
