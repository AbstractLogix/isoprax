"""Fail-closed execution evidence for an externally approved runner."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from .build_qualification import BuildPreparation
from .identity import bytes_hash, content_hash


@dataclass(frozen=True)
class ApprovedRunnerConfiguration:
    immutable_identity: str
    command: tuple[str, ...]
    timeout_seconds: int
    resource_limits: tuple[tuple[str, str], ...]
    network_disabled: bool
    source_read_only: bool
    work_storage_isolated: bool
    non_root: bool
    declared_artifacts: tuple[str, ...]


@dataclass(frozen=True)
class EffectiveRunnerControls:
    immutable_identity: str
    command: tuple[str, ...]
    source_commit: str
    timeout_seconds: int
    resource_limits: tuple[tuple[str, str], ...]
    network_disabled: bool
    source_read_only: bool
    work_storage_isolated: bool
    non_root: bool


@dataclass(frozen=True)
class RunnerBackendResult:
    effective_controls: EffectiveRunnerControls
    command_started: bool
    outcome: str
    reason: str
    duration_ms: int
    artifact_payloads: Mapping[str, object]


@dataclass(frozen=True)
class ArtifactEvidence:
    path: str
    state: str
    sha256: str | None = None
    byte_count: int | None = None


@dataclass(frozen=True)
class ExecutionEvidenceRecord:
    execution_identity: str
    preparation_hash: str
    commit: str
    configuration_identity: str
    command_identity: str
    effective_controls: EffectiveRunnerControls | None
    status: str
    reason: str
    command_started: bool
    duration_ms: int | None
    artifacts: tuple[ArtifactEvidence, ...]
    claim_scope: str = "execution_evidence_only"


RunnerBackend = Callable[[str, str, ApprovedRunnerConfiguration], RunnerBackendResult]
_VALID_OUTCOMES = {"success", "build_failed", "timeout", "interrupted", "unavailable"}


def _configuration_payload(
    configuration: ApprovedRunnerConfiguration,
) -> dict[str, object]:
    return {
        "immutable_identity": configuration.immutable_identity,
        "command": configuration.command,
        "timeout_seconds": configuration.timeout_seconds,
        "resource_limits": configuration.resource_limits,
        "network_disabled": configuration.network_disabled,
        "source_read_only": configuration.source_read_only,
        "work_storage_isolated": configuration.work_storage_isolated,
        "non_root": configuration.non_root,
        "declared_artifacts": configuration.declared_artifacts,
    }


def _controls_payload(controls: EffectiveRunnerControls | None) -> object:
    return None if controls is None else controls.__dict__


def _valid_artifact_path(path: str) -> bool:
    return bool(path) and not path.startswith("/") and ".." not in path.split("/")


def _configuration_error(configuration: ApprovedRunnerConfiguration) -> str | None:
    if "@sha256:" not in configuration.immutable_identity:
        return "runner identity is not immutable"
    if not configuration.command or any(
        not part.strip() for part in configuration.command
    ):
        return "runner command is not predeclared"
    if configuration.timeout_seconds <= 0:
        return "runner timeout is not positive"
    limits = configuration.resource_limits
    if (
        not limits
        or tuple(sorted(limits)) != limits
        or len({key for key, _ in limits}) != len(limits)
    ):
        return "runner resource limits are not canonical"
    if any(not key.strip() or not value.strip() for key, value in limits):
        return "runner resource limits are incomplete"
    if not configuration.network_disabled:
        return "runner network is not disabled"
    if not configuration.source_read_only:
        return "runner source input is not read-only"
    if not configuration.work_storage_isolated:
        return "runner work storage is not isolated"
    if not configuration.non_root:
        return "runner execution is not non-root"
    artifacts = configuration.declared_artifacts
    if len(set(artifacts)) != len(artifacts) or any(
        not _valid_artifact_path(path) for path in artifacts
    ):
        return "declared artifact paths are invalid"
    return None


def _controls_match(
    configuration: ApprovedRunnerConfiguration, controls: EffectiveRunnerControls
) -> bool:
    return (
        controls.immutable_identity == configuration.immutable_identity
        and controls.command == configuration.command
        and controls.timeout_seconds == configuration.timeout_seconds
        and controls.resource_limits == configuration.resource_limits
        and controls.network_disabled == configuration.network_disabled
        and controls.source_read_only == configuration.source_read_only
        and controls.work_storage_isolated == configuration.work_storage_isolated
        and controls.non_root == configuration.non_root
    )


def _artifacts(
    configuration: ApprovedRunnerConfiguration, payloads: Mapping[str, object]
) -> tuple[ArtifactEvidence, ...]:
    records = []
    for path in configuration.declared_artifacts:
        if path not in payloads:
            records.append(ArtifactEvidence(path, "missing"))
            continue
        payload = payloads[path]
        if payload is None or not isinstance(payload, bytes):
            records.append(ArtifactEvidence(path, "unreadable"))
            continue
        records.append(
            ArtifactEvidence(
                path,
                "collected",
                bytes_hash(payload),
                len(payload),
            )
        )
    return tuple(records)


def _record(
    preparation: BuildPreparation,
    commit: str,
    configuration: ApprovedRunnerConfiguration,
    *,
    status: str,
    reason: str,
    controls: EffectiveRunnerControls | None = None,
    command_started: bool = False,
    duration_ms: int | None = None,
    artifacts: tuple[ArtifactEvidence, ...] = (),
) -> ExecutionEvidenceRecord:
    configuration_identity = content_hash(_configuration_payload(configuration))
    command_identity = content_hash(configuration.command)
    execution_identity = content_hash(
        {
            "preparation_hash": preparation.preparation_hash,
            "commit": commit,
            "configuration": _configuration_payload(configuration),
            "effective_controls": _controls_payload(controls),
        }
    )
    return ExecutionEvidenceRecord(
        execution_identity,
        preparation.preparation_hash,
        commit,
        configuration_identity,
        command_identity,
        controls,
        status,
        reason,
        command_started,
        duration_ms,
        artifacts,
    )


def run_prepared_execution(
    preparation: BuildPreparation,
    commit: str,
    configuration: ApprovedRunnerConfiguration,
    backend: RunnerBackend,
) -> ExecutionEvidenceRecord:
    """Run one prepared commit through an approved injected backend.

    The backend is responsible for the external process/container. This module
    retains only evidence after independently checking its reported controls.
    """
    if preparation.blocked_reason:
        return _record(
            preparation,
            commit,
            configuration,
            status="blocked-before-compilation",
            reason=preparation.blocked_reason,
        )
    if commit not in preparation.sample.commits:
        return _record(
            preparation,
            commit,
            configuration,
            status="blocked-before-compilation",
            reason="commit is not in prepared sample",
        )
    if configuration.immutable_identity != preparation.sample.runner.immutable_identity:
        return _record(
            preparation,
            commit,
            configuration,
            status="blocked-before-compilation",
            reason="runner identity does not match preparation",
        )
    configuration_error = _configuration_error(configuration)
    if configuration_error:
        return _record(
            preparation,
            commit,
            configuration,
            status="blocked-before-compilation",
            reason=configuration_error,
        )
    try:
        result = backend(commit, preparation.sample.recipe_reference, configuration)
    except Exception as error:  # external backend boundary
        return _record(
            preparation,
            commit,
            configuration,
            status="blocked-before-compilation",
            reason=f"runner unavailable: {error}",
        )
    if not isinstance(result, RunnerBackendResult):
        return _record(
            preparation,
            commit,
            configuration,
            status="blocked-before-compilation",
            reason="runner returned an invalid result",
        )
    controls = result.effective_controls
    if not isinstance(controls, EffectiveRunnerControls):
        return _record(
            preparation,
            commit,
            configuration,
            status="blocked-before-compilation",
            reason="runner effective controls are invalid",
        )
    if not _controls_match(configuration, controls):
        return _record(
            preparation,
            commit,
            configuration,
            status="blocked-before-compilation",
            reason="runner effective controls do not match configuration",
            controls=controls,
        )
    if controls.source_commit != commit:
        return _record(
            preparation,
            commit,
            configuration,
            status="blocked-before-compilation",
            reason="runner source input does not match prepared commit",
            controls=controls,
        )
    if (
        not isinstance(result.duration_ms, int)
        or isinstance(result.duration_ms, bool)
        or result.duration_ms < 0
    ):
        return _record(
            preparation,
            commit,
            configuration,
            status="blocked-before-compilation",
            reason="runner duration is invalid",
            controls=controls,
        )
    if not isinstance(result.command_started, bool):
        return _record(
            preparation,
            commit,
            configuration,
            status="blocked-before-compilation",
            reason="runner command_started is invalid",
            controls=controls,
            duration_ms=result.duration_ms,
        )
    if not isinstance(result.artifact_payloads, Mapping):
        return _record(
            preparation,
            commit,
            configuration,
            status="blocked-before-compilation",
            reason="runner artifact payloads are invalid",
            controls=controls,
            duration_ms=result.duration_ms,
            command_started=result.command_started,
        )
    if not isinstance(result.outcome, str) or result.outcome not in _VALID_OUTCOMES:
        return _record(
            preparation,
            commit,
            configuration,
            status="blocked-before-compilation",
            reason="runner outcome is invalid",
            controls=controls,
            duration_ms=result.duration_ms,
            command_started=result.command_started,
        )
    if not result.command_started:
        return _record(
            preparation,
            commit,
            configuration,
            status="blocked-before-compilation",
            reason=result.reason or "runner command did not start",
            controls=controls,
            duration_ms=result.duration_ms,
            command_started=False,
        )
    artifacts = _artifacts(configuration, result.artifact_payloads)
    status = "success" if result.outcome == "success" else "censored"
    return _record(
        preparation,
        commit,
        configuration,
        status=status,
        reason=result.reason or result.outcome,
        controls=controls,
        command_started=True,
        duration_ms=result.duration_ms,
        artifacts=artifacts,
    )


__all__ = [
    "ApprovedRunnerConfiguration",
    "ArtifactEvidence",
    "EffectiveRunnerControls",
    "ExecutionEvidenceRecord",
    "RunnerBackend",
    "RunnerBackendResult",
    "run_prepared_execution",
]
