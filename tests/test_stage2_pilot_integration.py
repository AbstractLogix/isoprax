from isoprax.build_qualification import (
    BuildSample,
    LegalCoverageRecord,
    RunnerDescriptor,
    execute_prepared_sample,
    prepare_build_sample,
    reduce_build_qualification,
)
from isoprax.commensurability import OutcomeDefinition
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
from isoprax.stage2_feasibility import (
    ReplayPilotProfile,
    build_stage2_feasibility_report,
    normalize_replay_records,
    validate_stage2_feasibility_report,
)

COMMITS = ("commit-a", "commit-b")
RUNNER_ID = "registry.invalid/isoprax-pilot@sha256:" + "a" * 64


def _profile() -> ReplayPilotProfile:
    definition = OutcomeDefinition(
        "replay.threshold.v1",
        "latency threshold crossed",
        {"kind": "replay_telemetry", "parameters": {"metric": "p99"}},
        {"duration": 10, "unit": "minute", "anchor": "score_time"},
        ({"metric": "p99", "operator": ">", "value": 500},),
    )
    return ReplayPilotProfile(
        "synthetic-public-candidate",
        "demo-system",
        "demo-service",
        COMMITS,
        "workload-v1",
        definition,
        OutcomeDefinition(
            "replay.threshold.v1.operational",
            definition.event,
            definition.observation_process,
            definition.window,
            definition.thresholds,
        ),
        "PT10M",
        "threshold-v1",
        "capture-v1",
        "public-replay",
        ("manifest.json",),
        "predeclared-sha256",
        "anchor://stage2-pilot",
        "predeclaration-commit",
        ("corpus-data-commit",),
        True,
        frozenset({"diff_size"}),
        frozenset({"future_metric"}),
        2,
        True,
        1.0,
        False,
    )


def _build_and_execute():
    sample = BuildSample(
        COMMITS,
        "recipe://demo-build",
        tuple(LegalCoverageRecord(commit, f"license://{commit}") for commit in COMMITS),
        RunnerDescriptor(RUNNER_ID, True, True),
    )
    preparation = prepare_build_sample(sample)
    build_rows = execute_prepared_sample(
        preparation,
        lambda commit, recipe, runner: {
            "status": "success",
            "reason": f"built {commit}",
        },
    )
    qualification = reduce_build_qualification(
        preparation, build_rows, frozen_build_floor=1.0
    )
    configuration = ApprovedRunnerConfiguration(
        RUNNER_ID,
        ("/bin/true",),
        60,
        (("cpu", "1"),),
        True,
        True,
        True,
        True,
        ("build.log",),
    )

    def runner_backend(commit, recipe, config):
        controls = EffectiveRunnerControls(
            config.immutable_identity,
            config.command,
            commit,
            config.timeout_seconds,
            config.resource_limits,
            config.network_disabled,
            config.source_read_only,
            config.work_storage_isolated,
            config.non_root,
        )
        return RunnerBackendResult(
            controls, True, "success", "built", 10, {"build.log": b"ok"}
        )

    executions = tuple(
        run_prepared_execution(preparation, commit, configuration, runner_backend)
        for commit in COMMITS
    )

    def capture_backend(lane, report, execution):
        deployment = DeploymentEvidence(
            f"target-{lane.commit}",
            lane.commit,
            "succeeded",
            "2026-09-02T00:00:01Z",
            "2026-09-02T00:00:02Z",
            f"deploy://{lane.commit}",
        )
        observation = ObservationEvidence(
            lane.score_time,
            lane.window_start,
            lane.window_end,
            True,
            True,
            True,
            lane.commit == "commit-a",
            False,
            False,
            lane.allowed_evidence_scope,
            ("metrics.json",),
            {"metrics.json": b"public-metrics"},
            "synthetic observation",
        )
        return ReplayCaptureBackendResult(deployment, observation)

    captures = tuple(
        capture_replay_lane(
            ReplayLaneDefinition(
                "demo-system",
                "demo-service",
                commit,
                "workload-v1",
                "PT10M",
                "threshold-v1",
                "capture-v1",
                "public-replay",
                "2026-09-02T00:00:00Z",
                "2026-09-02T00:00:00Z",
                "2026-09-02T00:10:00Z",
            ),
            qualification,
            execution,
            capture_backend,
        )
        for commit, execution in zip(COMMITS, executions)
    )
    return captures


def test_injected_pilot_exercises_build_runner_capture_and_feasibility_report():
    pilot = _profile()
    captures = _build_and_execute()
    records = normalize_replay_records(
        pilot,
        captures,
        run_identity="synthetic-run-1",
        prediction_fields={
            commit: {"diff_size": "2026-09-01T23:59:00Z"} for commit in COMMITS
        },
    )
    report = build_stage2_feasibility_report(
        pilot,
        records,
        throughput={"build": 0.02, "deployment": 0.02, "observation": 0.1},
        extrapolation={"basis": "synthetic pilot only", "uncertainty": "not measured"},
    )
    validate_stage2_feasibility_report(report)
    assert report.status == "feasible"
    assert report.counts == {
        "selected": 2,
        "terminal": 2,
        "complete_observations": 2,
        "observed_positive": 1,
        "observed_negative": 1,
        "censored": 0,
        "blocked_before_compilation": 0,
        "release_withheld": 0,
    }
    assert report.temporal_coverage["complete_windows"] == 2
