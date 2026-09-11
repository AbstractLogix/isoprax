"""Deterministic, fail-closed replay deployment and observation evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Mapping

from .build_qualification import BuildQualificationReport
from .hermetic_runner import ExecutionEvidenceRecord
from .identity import bytes_hash, content_hash


@dataclass(frozen=True)
class ReplayLaneDefinition:
    system_id: str
    service_id: str
    commit: str
    workload_reference: str
    horizon_rule: str
    outcome_threshold_rule: str
    capture_schema_version: str
    allowed_evidence_scope: str
    score_time: str
    window_start: str
    window_end: str

    def __post_init__(self) -> None:
        for field_name in (
            "system_id",
            "service_id",
            "commit",
            "workload_reference",
            "horizon_rule",
            "outcome_threshold_rule",
            "capture_schema_version",
            "allowed_evidence_scope",
        ):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} is required")
        if _parse_utc(self.score_time) != _parse_utc(self.window_start):
            raise ValueError("score_time must equal window_start")
        if _parse_utc(self.window_start) >= _parse_utc(self.window_end):
            raise ValueError("observation window must be ordered")


@dataclass(frozen=True)
class DeploymentEvidence:
    target_id: str
    deployed_commit: str
    disposition: str
    started_at: str
    completed_at: str
    evidence_reference: str = ""


@dataclass(frozen=True)
class ObservationEvidence:
    score_time: str
    window_start: str
    window_end: str
    window_complete: bool
    monitoring_complete: bool
    valid: bool
    threshold_met: bool
    uses_private_production_data: bool
    uses_privileged_telemetry: bool
    evidence_scope: str
    declared_artifacts: tuple[str, ...]
    artifact_payloads: Mapping[str, object]
    reason: str = ""


@dataclass(frozen=True)
class ObservationArtifactEvidence:
    path: str
    state: str
    sha256: str | None = None
    byte_count: int | None = None


@dataclass(frozen=True)
class ReplayCaptureBackendResult:
    deployment: DeploymentEvidence
    observation: ObservationEvidence | None = None


@dataclass(frozen=True)
class ReplayCaptureRecord:
    lane_identity: str
    lane: ReplayLaneDefinition
    qualification_report_hash: str
    execution_identity: str
    deployment: DeploymentEvidence | None
    observation: ObservationEvidence | None
    artifacts: tuple[ObservationArtifactEvidence, ...]
    outcome_class: str
    censor_reason: str | None
    claim_scope: str = "replay_observation_evidence_only"


ReplayCaptureBackend = Callable[
    [ReplayLaneDefinition, BuildQualificationReport, ExecutionEvidenceRecord],
    ReplayCaptureBackendResult,
]
_DEPLOYMENT_DISPOSITIONS = {
    "succeeded",
    "failed",
    "unverifiable",
    "rolled_back",
    "replaced",
}


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must be RFC 3339 UTC")
    try:
        return datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as error:
        raise ValueError("timestamp must be RFC 3339 UTC") from error


def _valid_path(path: str) -> bool:
    return bool(path) and not path.startswith("/") and ".." not in path.split("/")


def _lane_payload(lane: ReplayLaneDefinition) -> dict[str, object]:
    return lane.__dict__.copy()


def _deployment_payload(deployment: DeploymentEvidence | None) -> object:
    if deployment is None:
        return None
    if not isinstance(deployment, DeploymentEvidence):
        return {"invalid_type": type(deployment).__name__}
    return deployment.__dict__.copy()


def _artifact_records(
    observation: ObservationEvidence,
) -> tuple[ObservationArtifactEvidence, ...]:
    if (
        not isinstance(observation.declared_artifacts, tuple)
        or len(set(observation.declared_artifacts))
        != len(observation.declared_artifacts)
        or any(not _valid_path(path) for path in observation.declared_artifacts)
    ):
        raise ValueError("observation artifact declarations are invalid")
    if not isinstance(observation.artifact_payloads, Mapping):
        raise ValueError("observation artifact payloads are invalid")
    if set(observation.artifact_payloads) - set(observation.declared_artifacts):
        raise ValueError("observation has undeclared artifact payloads")
    records = []
    for path in observation.declared_artifacts:
        if path not in observation.artifact_payloads:
            records.append(ObservationArtifactEvidence(path, "missing"))
            continue
        payload = observation.artifact_payloads[path]
        if not isinstance(payload, bytes):
            records.append(ObservationArtifactEvidence(path, "unreadable"))
            continue
        records.append(
            ObservationArtifactEvidence(
                path, "collected", bytes_hash(payload), len(payload)
            )
        )
    return tuple(records)


def _observation_payload(
    observation: ObservationEvidence | None,
    artifacts: tuple[ObservationArtifactEvidence, ...],
) -> object:
    if observation is None:
        return None
    if not isinstance(observation, ObservationEvidence):
        return {"invalid_type": type(observation).__name__}
    return {
        "score_time": observation.score_time,
        "window_start": observation.window_start,
        "window_end": observation.window_end,
        "window_complete": observation.window_complete,
        "monitoring_complete": observation.monitoring_complete,
        "valid": observation.valid,
        "threshold_met": observation.threshold_met,
        "uses_private_production_data": observation.uses_private_production_data,
        "uses_privileged_telemetry": observation.uses_privileged_telemetry,
        "evidence_scope": observation.evidence_scope,
        "declared_artifacts": observation.declared_artifacts,
        "reason": observation.reason,
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


def _record(
    lane: ReplayLaneDefinition,
    report: BuildQualificationReport,
    execution: ExecutionEvidenceRecord,
    *,
    deployment: DeploymentEvidence | None = None,
    observation: ObservationEvidence | None = None,
    artifacts: tuple[ObservationArtifactEvidence, ...] = (),
    outcome_class: str = "censored",
    censor_reason: str | None = None,
) -> ReplayCaptureRecord:
    identity = content_hash(
        {
            "lane": _lane_payload(lane),
            "qualification_report_hash": report.preparation_hash,
            "execution_identity": execution.execution_identity,
            "deployment": _deployment_payload(deployment),
            "observation": _observation_payload(observation, artifacts),
            "outcome_class": outcome_class,
            "censor_reason": censor_reason,
        }
    )
    return ReplayCaptureRecord(
        identity,
        lane,
        report.preparation_hash,
        execution.execution_identity,
        deployment,
        observation,
        artifacts,
        outcome_class,
        censor_reason,
    )


def _upstream_error(
    lane: ReplayLaneDefinition,
    report: BuildQualificationReport,
    execution: ExecutionEvidenceRecord,
) -> str | None:
    if not report.qualified:
        return "build qualification is not qualified"
    rows = {row.commit: row for row in report.rows}
    if rows.get(lane.commit) is None or rows[lane.commit].status != "success":
        return "lane commit lacks successful build qualification evidence"
    if execution.preparation_hash != report.preparation_hash:
        return "execution preparation does not match qualification report"
    if execution.commit != lane.commit:
        return "execution commit does not match lane"
    if execution.status != "success":
        return "execution is not a successful deployable build"
    return None


def _deployment_error(
    lane: ReplayLaneDefinition, deployment: DeploymentEvidence
) -> str | None:
    if not isinstance(deployment, DeploymentEvidence):
        return "deployment evidence is invalid"
    if (
        not deployment.target_id.strip()
        or not deployment.deployed_commit.strip()
        or deployment.disposition not in _DEPLOYMENT_DISPOSITIONS
    ):
        return "deployment evidence is incomplete"
    try:
        if _parse_utc(deployment.started_at) > _parse_utc(deployment.completed_at):
            return "deployment timestamps are unordered"
    except ValueError:
        return "deployment timestamps are invalid"
    if deployment.deployed_commit != lane.commit:
        return "deployment commit does not match lane"
    if deployment.disposition != "succeeded":
        return f"deployment {deployment.disposition}"
    if not deployment.evidence_reference.strip():
        return "successful deployment lacks evidence reference"
    return None


def _observation_error(
    lane: ReplayLaneDefinition, observation: ObservationEvidence
) -> tuple[str | None, tuple[ObservationArtifactEvidence, ...]]:
    if not isinstance(observation, ObservationEvidence):
        return "observation evidence is invalid", ()
    boolean_fields = (
        "window_complete",
        "monitoring_complete",
        "valid",
        "threshold_met",
        "uses_private_production_data",
        "uses_privileged_telemetry",
    )
    if any(
        not isinstance(getattr(observation, field), bool) for field in boolean_fields
    ):
        return "observation evidence has invalid boolean fields", ()
    try:
        times_match = (
            observation.score_time == lane.score_time
            and observation.window_start == lane.window_start
            and observation.window_end == lane.window_end
            and _parse_utc(observation.window_start)
            < _parse_utc(observation.window_end)
        )
    except ValueError:
        times_match = False
    if not times_match:
        return "observation window does not match frozen lane", ()
    if observation.uses_private_production_data:
        return "observation uses private production data", ()
    if observation.uses_privileged_telemetry:
        return "observation uses privileged telemetry", ()
    if (
        not isinstance(observation.evidence_scope, str)
        or observation.evidence_scope != lane.allowed_evidence_scope
    ):
        return "observation evidence scope does not match frozen lane", ()
    if not observation.window_complete:
        return "observation window is incomplete", ()
    if not observation.monitoring_complete:
        return "observation monitoring has a gap", ()
    if not observation.valid:
        return "observation evidence is invalid", ()
    if not isinstance(observation.reason, str):
        return "observation reason is invalid", ()
    try:
        artifacts = _artifact_records(observation)
    except ValueError as error:
        return str(error), ()
    return None, artifacts


def capture_replay_lane(
    lane: ReplayLaneDefinition,
    qualification_report: BuildQualificationReport,
    execution: ExecutionEvidenceRecord,
    backend: ReplayCaptureBackend,
) -> ReplayCaptureRecord:
    """Capture one frozen replay lane through the sole injected effect boundary."""
    error = _upstream_error(lane, qualification_report, execution)
    if error:
        return _record(lane, qualification_report, execution, censor_reason=error)
    try:
        result = backend(lane, qualification_report, execution)
    except Exception as error:  # external deployment/telemetry boundary
        return _record(
            lane,
            qualification_report,
            execution,
            censor_reason=f"capture backend unavailable: {error}",
        )
    if not isinstance(result, ReplayCaptureBackendResult):
        return _record(
            lane,
            qualification_report,
            execution,
            censor_reason="capture backend is invalid",
        )
    deployment_error = _deployment_error(lane, result.deployment)
    if deployment_error:
        return _record(
            lane,
            qualification_report,
            execution,
            deployment=result.deployment,
            censor_reason=deployment_error,
        )
    if result.observation is None:
        return _record(
            lane,
            qualification_report,
            execution,
            deployment=result.deployment,
            censor_reason="observation evidence is unavailable",
        )
    observation_error, artifacts = _observation_error(lane, result.observation)
    if observation_error:
        return _record(
            lane,
            qualification_report,
            execution,
            deployment=result.deployment,
            observation=result.observation,
            artifacts=artifacts,
            censor_reason=observation_error,
        )
    outcome_class = (
        "observed_positive" if result.observation.threshold_met else "observed_negative"
    )
    return _record(
        lane,
        qualification_report,
        execution,
        deployment=result.deployment,
        observation=result.observation,
        artifacts=artifacts,
        outcome_class=outcome_class,
    )


__all__ = [
    "DeploymentEvidence",
    "ObservationArtifactEvidence",
    "ObservationEvidence",
    "ReplayCaptureBackend",
    "ReplayCaptureBackendResult",
    "ReplayCaptureRecord",
    "ReplayLaneDefinition",
    "capture_replay_lane",
]
