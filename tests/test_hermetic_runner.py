from dataclasses import replace

from isoprax.build_qualification import (
    BuildSample,
    LegalCoverageRecord,
    RunnerDescriptor,
    prepare_build_sample,
)
from isoprax.hermetic_runner import (
    ApprovedRunnerConfiguration,
    EffectiveRunnerControls,
    RunnerBackendResult,
    run_prepared_execution,
)


def prepared_sample():
    commits = ("commit-a",)
    return prepare_build_sample(
        BuildSample(
            commits,
            "recipe-v1",
            (LegalCoverageRecord("commit-a", "LICENSES/commit-a"),),
            RunnerDescriptor("example@sha256:abc", True, True),
        )
    )


def configuration(**changes):
    base = ApprovedRunnerConfiguration(
        immutable_identity="example@sha256:abc",
        command=("./build", "--offline"),
        timeout_seconds=60,
        resource_limits=(("memory", "512m"),),
        network_disabled=True,
        source_read_only=True,
        work_storage_isolated=True,
        non_root=True,
        declared_artifacts=("out/result.txt", "out/log.txt"),
    )
    return replace(base, **changes)


def controls(config, commit="commit-a"):
    return EffectiveRunnerControls(
        immutable_identity=config.immutable_identity,
        command=config.command,
        source_commit=commit,
        timeout_seconds=config.timeout_seconds,
        resource_limits=config.resource_limits,
        network_disabled=config.network_disabled,
        source_read_only=config.source_read_only,
        work_storage_isolated=config.work_storage_isolated,
        non_root=config.non_root,
    )


def successful_backend(config, artifacts=None):
    return lambda *_: RunnerBackendResult(
        effective_controls=controls(config),
        command_started=True,
        outcome="success",
        reason="completed",
        duration_ms=12,
        artifact_payloads=artifacts or {"out/result.txt": b"result"},
    )


def test_runs_only_valid_prepared_configurations_and_preserves_frozen_inputs():
    prepared = prepared_sample()
    config = configuration()
    calls = []

    def backend(commit, recipe_reference, received_config):
        calls.append((commit, recipe_reference, received_config))
        return successful_backend(config)()

    record = run_prepared_execution(prepared, "commit-a", config, backend)

    assert record.status == "success"
    assert calls == [("commit-a", "recipe-v1", config)]
    assert record.preparation_hash == prepared.preparation_hash
    assert record.command_identity
    assert record.command_started is True


def test_invalid_or_unverified_controls_block_before_backend_invocation():
    prepared = prepared_sample()
    invalid_configs = (
        configuration(immutable_identity="example:latest"),
        configuration(network_disabled=False),
        configuration(source_read_only=False),
        configuration(work_storage_isolated=False),
        configuration(non_root=False),
        configuration(resource_limits=()),
    )
    for config in invalid_configs:
        record = run_prepared_execution(
            prepared, "commit-a", config, lambda *_: AssertionError("must not run")
        )
        assert record.status == "blocked-before-compilation"
        assert record.command_started is False

    config = configuration()
    mismatched = replace(controls(config), network_disabled=False)
    record = run_prepared_execution(
        prepared,
        "commit-a",
        config,
        lambda *_: RunnerBackendResult(
            mismatched, False, "unavailable", "mismatch", 0, {}
        ),
    )
    assert record.status == "blocked-before-compilation"
    assert record.command_started is False

    different_runner = configuration(immutable_identity="other@sha256:abc")
    assert (
        run_prepared_execution(
            prepared, "commit-a", different_runner, successful_backend(different_runner)
        ).status
        == "blocked-before-compilation"
    )

    wrong_source = replace(controls(config), source_commit="other-commit")
    assert (
        run_prepared_execution(
            prepared,
            "commit-a",
            config,
            lambda *_: RunnerBackendResult(
                wrong_source, False, "unavailable", "wrong", 0, {}
            ),
        ).status
        == "blocked-before-compilation"
    )


def test_retains_process_and_artifact_evidence_without_conflating_them():
    prepared = prepared_sample()
    config = configuration()
    record = run_prepared_execution(
        prepared,
        "commit-a",
        config,
        successful_backend(config, {"out/result.txt": b"result", "out/log.txt": None}),
    )

    assert record.status == "success"
    assert [artifact.state for artifact in record.artifacts] == [
        "collected",
        "unreadable",
    ]
    assert record.artifacts[0].sha256
    assert record.artifacts[1].sha256 is None

    for outcome in ("build_failed", "timeout", "interrupted"):
        censored = run_prepared_execution(
            prepared,
            "commit-a",
            config,
            lambda *_: RunnerBackendResult(
                controls(config), True, outcome, outcome, 1, {}
            ),
        )
        assert censored.status == "censored"


def test_identity_changes_for_material_changes_and_backend_errors_are_retained():
    prepared = prepared_sample()
    config = configuration()
    first = run_prepared_execution(
        prepared, "commit-a", config, successful_backend(config)
    )
    same = run_prepared_execution(
        prepared, "commit-a", config, successful_backend(config)
    )
    changed = run_prepared_execution(
        prepared,
        "commit-a",
        configuration(command=("./build", "--strict")),
        successful_backend(configuration(command=("./build", "--strict"))),
    )
    unavailable = run_prepared_execution(
        prepared,
        "commit-a",
        config,
        lambda *_: (_ for _ in ()).throw(RuntimeError("offline")),
    )

    assert first.execution_identity == same.execution_identity
    assert first.execution_identity != changed.execution_identity
    assert unavailable.status == "blocked-before-compilation"
    assert "runner unavailable" in unavailable.reason


def test_blocks_invalid_preparation_commits_and_remaining_configuration_failures():
    prepared = prepared_sample()
    config = configuration()
    blocked_preparation = prepare_build_sample(
        BuildSample(
            ("commit-a",),
            "recipe-v1",
            (LegalCoverageRecord("commit-a", "LICENSES/commit-a", covered=False),),
            RunnerDescriptor("example@sha256:abc", True, True),
        )
    )
    assert (
        run_prepared_execution(
            blocked_preparation, "commit-a", config, successful_backend(config)
        ).status
        == "blocked-before-compilation"
    )
    assert (
        run_prepared_execution(
            prepared, "outside-sample", config, successful_backend(config)
        ).status
        == "blocked-before-compilation"
    )

    for invalid in (
        configuration(command=()),
        configuration(timeout_seconds=0),
        configuration(resource_limits=(("z", "1"), ("a", "1"))),
        configuration(resource_limits=(("", "1"),)),
        configuration(declared_artifacts=("../escape",)),
    ):
        assert (
            run_prepared_execution(
                prepared, "commit-a", invalid, successful_backend(invalid)
            ).status
            == "blocked-before-compilation"
        )


def test_blocks_invalid_duration_and_command_not_started():
    prepared = prepared_sample()
    config = configuration()
    negative = run_prepared_execution(
        prepared,
        "commit-a",
        config,
        lambda *_: RunnerBackendResult(
            controls(config), True, "success", "bad", -1, {}
        ),
    )
    not_started = run_prepared_execution(
        prepared,
        "commit-a",
        config,
        lambda *_: RunnerBackendResult(
            controls(config), False, "unavailable", "offline", 0, {}
        ),
    )

    assert negative.status == "blocked-before-compilation"
    assert not_started.status == "blocked-before-compilation"
    assert not_started.duration_ms == 0
    assert (
        run_prepared_execution(prepared, "commit-a", config, lambda *_: None).status
        == "blocked-before-compilation"
    )
