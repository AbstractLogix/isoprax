from dataclasses import replace

from isoprax.build_qualification import (
    BuildRowResult,
    BuildSample,
    LegalCoverageRecord,
    RunnerDescriptor,
    prepare_build_sample,
    reduce_build_qualification,
)
from isoprax.hermetic_runner import (
    ApprovedRunnerConfiguration,
    EffectiveRunnerControls,
    RunnerBackendResult,
    run_prepared_execution,
)
from isoprax.replay_capture import (
    DeploymentEvidence,
    ObservationEvidence,
    ReplayCaptureBackendResult,
    ReplayLaneDefinition,
    capture_replay_lane,
)


def qualification_report():
    sample = BuildSample(
        ("commit-a",),
        "recipe-v1",
        (LegalCoverageRecord("commit-a", "LICENSES/commit-a"),),
        RunnerDescriptor("example@sha256:abc", True, True),
    )
    preparation = prepare_build_sample(sample)
    report = reduce_build_qualification(
        preparation,
        (BuildRowResult("commit-a", "success", "completed"),),
        frozen_build_floor=1.0,
    )
    return preparation, report


def configuration():
    return ApprovedRunnerConfiguration(
        immutable_identity="example@sha256:abc",
        command=("./build", "--offline"),
        timeout_seconds=60,
        resource_limits=(("memory", "512m"),),
        network_disabled=True,
        source_read_only=True,
        work_storage_isolated=True,
        non_root=True,
        declared_artifacts=(),
    )


def successful_execution(preparation):
    config = configuration()
    controls = EffectiveRunnerControls(
        immutable_identity=config.immutable_identity,
        command=config.command,
        source_commit="commit-a",
        timeout_seconds=config.timeout_seconds,
        resource_limits=config.resource_limits,
        network_disabled=config.network_disabled,
        source_read_only=config.source_read_only,
        work_storage_isolated=config.work_storage_isolated,
        non_root=config.non_root,
    )
    return run_prepared_execution(
        preparation,
        "commit-a",
        config,
        lambda *_: RunnerBackendResult(controls, True, "success", "completed", 1, {}),
    )


def lane(**changes):
    base = ReplayLaneDefinition(
        system_id="system-a",
        service_id="service-a",
        commit="commit-a",
        workload_reference="workload-v1",
        horizon_rule="PT10M",
        outcome_threshold_rule="error-rate >= 1%",
        capture_schema_version="v1",
        allowed_evidence_scope="public synthetic replay evidence",
        score_time="2026-09-06T00:00:00Z",
        window_start="2026-09-06T00:00:00Z",
        window_end="2026-09-06T00:10:00Z",
    )
    return replace(base, **changes)


def successful_result(**changes):
    deployment = DeploymentEvidence(
        target_id="target-a",
        deployed_commit="commit-a",
        disposition="succeeded",
        started_at="2026-09-06T00:00:01Z",
        completed_at="2026-09-06T00:00:02Z",
        evidence_reference="deployment/1",
    )
    observation = ObservationEvidence(
        score_time="2026-09-06T00:00:00Z",
        window_start="2026-09-06T00:00:00Z",
        window_end="2026-09-06T00:10:00Z",
        window_complete=True,
        monitoring_complete=True,
        valid=True,
        threshold_met=True,
        uses_private_production_data=False,
        uses_privileged_telemetry=False,
        evidence_scope="public synthetic replay evidence",
        declared_artifacts=("metrics.json", "logs.txt"),
        artifact_payloads={"metrics.json": b"metrics", "logs.txt": None},
        reason="observed",
    )
    return replace(ReplayCaptureBackendResult(deployment, observation), **changes)


def capture(result=None, **lane_changes):
    preparation, report = qualification_report()
    execution = successful_execution(preparation)
    result = result or successful_result()
    return capture_replay_lane(
        lane(**lane_changes), report, execution, lambda *_: result
    )


def test_captures_complete_lane_and_preserves_lineage():
    record = capture()

    assert record.outcome_class == "observed_positive"
    assert record.censor_reason is None
    assert record.qualification_report_hash
    assert record.execution_identity
    assert record.deployment is not None
    assert record.observation is not None
    assert record.claim_scope == "replay_observation_evidence_only"
    assert [artifact.state for artifact in record.artifacts] == [
        "collected",
        "unreadable",
    ]
    assert record.artifacts[0].sha256


def test_equivalent_inputs_are_stable_and_material_changes_differ():
    first = capture()
    same = capture()
    changed = capture(workload_reference="workload-v2")

    assert first.lane_identity == same.lane_identity
    assert first.lane_identity != changed.lane_identity


def test_ineligible_or_mismatched_upstream_evidence_is_censored_without_backend_call():
    preparation, report = qualification_report()
    execution = successful_execution(preparation)
    unqualified = replace(report, qualified=False)
    called = []

    record = capture_replay_lane(
        lane(), unqualified, execution, lambda *_: called.append(True)
    )
    mismatch = capture_replay_lane(
        lane(commit="other-commit"), report, execution, lambda *_: called.append(True)
    )

    assert record.outcome_class == "censored"
    assert "not qualified" in record.censor_reason
    assert mismatch.outcome_class == "censored"
    assert "commit" in mismatch.censor_reason
    assert not called


def test_deployment_and_observation_failures_are_censored_never_negative():
    failures = (
        successful_result(
            deployment=replace(successful_result().deployment, disposition="failed")
        ),
        successful_result(
            deployment=replace(
                successful_result().deployment, deployed_commit="other-commit"
            )
        ),
        successful_result(
            observation=replace(successful_result().observation, window_complete=False)
        ),
        successful_result(
            observation=replace(
                successful_result().observation, monitoring_complete=False
            )
        ),
        successful_result(
            observation=replace(
                successful_result().observation,
                window_end="2026-09-06T00:11:00Z",
            )
        ),
    )
    for result in failures:
        record = capture(result)
        assert record.outcome_class == "censored"
        assert record.censor_reason


def test_complete_threshold_miss_is_observed_negative():
    record = capture(
        successful_result(
            observation=replace(successful_result().observation, threshold_met=False)
        )
    )

    assert record.outcome_class == "observed_negative"


def test_scope_artifact_and_backend_errors_are_explicitly_retained():
    private = capture(
        successful_result(
            observation=replace(
                successful_result().observation,
                uses_private_production_data=True,
            )
        )
    )
    unavailable = capture_replay_lane(
        lane(),
        qualification_report()[1],
        successful_execution(qualification_report()[0]),
        lambda *_: (_ for _ in ()).throw(RuntimeError("offline")),
    )

    assert private.outcome_class == "censored"
    assert "private" in private.censor_reason
    assert unavailable.outcome_class == "censored"
    assert "backend unavailable" in unavailable.censor_reason


def test_invalid_lane_and_backend_contract_inputs_are_rejected_or_censored():
    try:
        lane(service_id="")
    except ValueError as error:
        assert "service_id" in str(error)
    else:
        raise AssertionError("invalid lane must be rejected")

    malformed = capture(
        ReplayCaptureBackendResult(
            successful_result().deployment,
            replace(successful_result().observation, declared_artifacts=("../bad",)),
        )
    )
    assert malformed.outcome_class == "censored"
    assert "artifact" in malformed.censor_reason


def test_all_non_success_deployment_dispositions_and_missing_observation_censor():
    for disposition in ("failed", "unverifiable", "rolled_back", "replaced"):
        record = capture(
            successful_result(
                deployment=replace(
                    successful_result().deployment, disposition=disposition
                )
            )
        )
        assert record.outcome_class == "censored"
        assert disposition in record.censor_reason

    assert capture(successful_result(observation=None)).outcome_class == "censored"


def test_privileged_or_invalid_observation_contract_is_censored():
    privileged = capture(
        successful_result(
            observation=replace(
                successful_result().observation, uses_privileged_telemetry=True
            )
        )
    )
    invalid_boolean = capture(
        successful_result(observation=replace(successful_result().observation, valid=1))
    )
    extra_payload = capture(
        successful_result(
            observation=replace(
                successful_result().observation,
                artifact_payloads={"metrics.json": b"metrics", "extra": b"bad"},
            )
        )
    )

    assert privileged.outcome_class == "censored"
    assert "privileged" in privileged.censor_reason
    assert invalid_boolean.outcome_class == "censored"
    assert extra_payload.outcome_class == "censored"


def test_preparation_mismatch_and_invalid_backend_result_are_censored():
    preparation, report = qualification_report()
    execution = successful_execution(preparation)
    mismatched = capture_replay_lane(
        lane(), replace(report, preparation_hash="other"), execution, lambda *_: None
    )
    invalid_result = capture_replay_lane(lane(), report, execution, lambda *_: None)

    assert mismatched.outcome_class == "censored"
    assert "preparation" in mismatched.censor_reason
    assert invalid_result.outcome_class == "censored"
    assert "backend is invalid" in invalid_result.censor_reason


def test_unqualified_commit_row_or_mismatched_evidence_scope_is_censored():
    preparation, report = qualification_report()
    execution = successful_execution(preparation)
    failed_row = replace(
        report,
        rows=(BuildRowResult("commit-a", "censored", "failed"),),
    )
    failed_build = capture_replay_lane(
        lane(), failed_row, execution, lambda *_: successful_result()
    )
    wrong_scope = capture(
        successful_result(
            observation=replace(
                successful_result().observation, evidence_scope="different scope"
            )
        )
    )

    assert failed_build.outcome_class == "censored"
    assert "successful build qualification" in failed_build.censor_reason
    assert wrong_scope.outcome_class == "censored"
    assert "scope" in wrong_scope.censor_reason
