"""Deterministic assembly of replay-capture evidence into Stage 1 rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping

from .admission import CorpusRow, SplitDefinition
from .identity import content_hash
from .replay_capture import ReplayCaptureRecord

_SPLIT_NAMES = ("train", "calibration_fit", "calibration_gate", "test")


@dataclass(frozen=True)
class CorpusAssemblyProfile:
    expected_system_id: str
    horizon_rule: str
    threshold_version: str
    release_scope: str
    allowed_prediction_fields: frozenset[str]
    forbidden_prediction_fields: frozenset[str]
    split_definitions: tuple[
        SplitDefinition, SplitDefinition, SplitDefinition, SplitDefinition
    ]
    published_artifacts: tuple[str, ...]

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.expected_system_id,
                self.horizon_rule,
                self.threshold_version,
                self.release_scope,
            )
        ):
            raise ValueError("assembly profile metadata is required")
        if tuple(split.name for split in self.split_definitions) != _SPLIT_NAMES:
            raise ValueError("split definitions must be canonical")
        for previous, current in zip(
            self.split_definitions, self.split_definitions[1:]
        ):
            if _parse_time(previous.end) > _parse_time(current.start):
                raise ValueError("split definitions must not overlap")
        if not self.published_artifacts or not all(
            artifact.strip() for artifact in self.published_artifacts
        ):
            raise ValueError("published artifacts are required")


@dataclass(frozen=True)
class ReplayCaptureInput:
    capture: ReplayCaptureRecord
    prediction_fields: Mapping[str, Any]
    field_observed_at: Mapping[str, str]


@dataclass(frozen=True)
class AssemblyRejection:
    input_identity: str
    reason: str


@dataclass(frozen=True)
class CorpusAssemblyReport:
    profile_identity: str
    rows: tuple[CorpusRow, ...]
    rejections: tuple[AssemblyRejection, ...]
    counts: dict[str, int]
    manifest_input: dict[str, Any]
    claim_scope: str = "corpus_assembly_evidence_only"


def _parse_time(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _admission_timestamp(value: str) -> str:
    """Normalize a validated capture timestamp for the Python 3.10 row contract."""
    return _parse_time(value).isoformat()


def _profile_payload(profile: CorpusAssemblyProfile) -> dict[str, object]:
    return {
        "expected_system_id": profile.expected_system_id,
        "horizon_rule": profile.horizon_rule,
        "threshold_version": profile.threshold_version,
        "release_scope": profile.release_scope,
        "allowed_prediction_fields": sorted(profile.allowed_prediction_fields),
        "forbidden_prediction_fields": sorted(profile.forbidden_prediction_fields),
        "splits": [split.__dict__ for split in profile.split_definitions],
        "published_artifacts": profile.published_artifacts,
    }


def _input_identity(value: ReplayCaptureInput) -> str:
    capture = value.capture
    identity = getattr(capture, "lane_identity", type(capture).__name__)
    return content_hash(
        {
            "capture": identity,
            "fields": value.prediction_fields,
            "observed_at": value.field_observed_at,
        }
    )


def _split_for(
    profile: CorpusAssemblyProfile, score_time: str
) -> SplitDefinition | None:
    timestamp = _parse_time(score_time)
    for split in profile.split_definitions:
        if _parse_time(split.start) <= timestamp <= _parse_time(split.end):
            return split
    return None


def _validate(
    profile: CorpusAssemblyProfile, value: ReplayCaptureInput, seen_changes: set[str]
) -> tuple[str | None, SplitDefinition | None]:
    capture = value.capture
    if not isinstance(capture, ReplayCaptureRecord):
        return "capture record is invalid", None
    if capture.claim_scope != "replay_observation_evidence_only":
        return "capture claim scope is invalid", None
    if capture.deployment is None or capture.observation is None:
        return "capture lineage is incomplete", None
    lane = capture.lane
    if (
        lane.system_id != profile.expected_system_id
        or lane.horizon_rule != profile.horizon_rule
        or lane.outcome_threshold_rule != profile.threshold_version
        or lane.allowed_evidence_scope != profile.release_scope
    ):
        return "capture does not match frozen assembly profile", None
    change_id = lane.commit
    if change_id in seen_changes:
        return "duplicate change in assembly", None
    if capture.outcome_class not in {
        "observed_positive",
        "observed_negative",
        "censored",
    }:
        return "capture outcome class is invalid", None
    if capture.outcome_class == "censored" and not capture.censor_reason:
        return "censored capture lacks reason", None
    fields = value.prediction_fields
    observed_at = value.field_observed_at
    if not isinstance(fields, Mapping) or not isinstance(observed_at, Mapping):
        return "prediction fields are invalid", None
    keys = set(fields)
    if (
        keys - set(profile.allowed_prediction_fields)
        or keys & set(profile.forbidden_prediction_fields)
        or set(observed_at) != keys
    ):
        return "prediction fields violate frozen profile", None
    try:
        score_time = _parse_time(lane.score_time)
        if any(
            _parse_time(timestamp) > score_time for timestamp in observed_at.values()
        ):
            return "prediction field is post-score-time", None
        split = _split_for(profile, lane.score_time)
        if split is None:
            return "score time is outside frozen splits", None
        if capture.outcome_class != "censored" and _parse_time(
            lane.window_end
        ) > _parse_time(split.end):
            return "observation follow-up exceeds frozen split", None
    except (TypeError, ValueError):
        return "capture or field timestamps are invalid", None
    return None, split


def _row(
    profile_identity: str,
    value: ReplayCaptureInput,
    split: SplitDefinition,
) -> CorpusRow:
    capture = value.capture
    lane = capture.lane
    row_id = content_hash(
        {
            "profile": profile_identity,
            "capture": capture.lane_identity,
            "fields": value.prediction_fields,
            "observed_at": value.field_observed_at,
        }
    )
    return CorpusRow(
        row_id=row_id,
        system_id=lane.system_id,
        change_id=lane.commit,
        deployment_id=capture.deployment.evidence_reference,
        observation_id=capture.lane_identity,
        split=split.name,
        score_time=_admission_timestamp(lane.score_time),
        outcome_class=capture.outcome_class,
        prediction_fields=dict(value.prediction_fields),
        linkage_bases=("immutable_capture_lineage",),
        outcome_window_complete=capture.observation.window_complete,
        horizon_rule_used=lane.horizon_rule,
        threshold_version=lane.outcome_threshold_rule,
        change_group_id=lane.commit,
        censor_reason=capture.censor_reason,
        prediction_field_observed_at={
            name: _admission_timestamp(timestamp)
            for name, timestamp in value.field_observed_at.items()
        },
        build_succeeded=capture.outcome_class != "censored",
        deployment_succeeded=capture.deployment.disposition == "succeeded",
        monitoring_complete=capture.observation.monitoring_complete,
    )


def assemble_corpus(
    profile: CorpusAssemblyProfile, inputs: Iterable[ReplayCaptureInput]
) -> CorpusAssemblyReport:
    """Reduce capture evidence into deterministic candidate rows and rejections."""
    profile_identity = content_hash(_profile_payload(profile))
    accepted: list[CorpusRow] = []
    rejected: list[AssemblyRejection] = []
    seen_changes: set[str] = set()
    for value in sorted(tuple(inputs), key=_input_identity):
        identity = _input_identity(value)
        error, split = _validate(profile, value, seen_changes)
        if error:
            rejected.append(AssemblyRejection(identity, error))
            continue
        seen_changes.add(value.capture.lane.commit)
        accepted.append(_row(profile_identity, value, split))
    rows = tuple(sorted(accepted, key=lambda row: (row.change_id, row.row_id)))
    rejections = tuple(sorted(rejected, key=lambda rejection: rejection.input_identity))
    counts = {
        outcome: sum(row.outcome_class == outcome for row in rows)
        for outcome in ("observed_positive", "observed_negative", "censored")
    }
    manifest = {
        "profile_identity": profile_identity,
        "source_system": profile.expected_system_id,
        "release_scope": profile.release_scope,
        "horizon_rule": profile.horizon_rule,
        "threshold_version": profile.threshold_version,
        "splits": [split.__dict__ for split in profile.split_definitions],
        "counts": counts,
        "published_artifacts": profile.published_artifacts,
        "rejection_count": len(rejections),
    }
    return CorpusAssemblyReport(profile_identity, rows, rejections, counts, manifest)


__all__ = [
    "AssemblyRejection",
    "CorpusAssemblyProfile",
    "CorpusAssemblyReport",
    "ReplayCaptureInput",
    "assemble_corpus",
]
