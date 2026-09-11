"""Offline normalization of supplied public corpus materialization snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .identity import bytes_hash, content_hash

_CANONICAL_SPLITS = ("train", "calibration_fit", "calibration_gate", "test")
_ALLOWED_OUTCOMES = ("observed_positive", "observed_negative", "censored")


@dataclass(frozen=True)
class PublicCorpusMaterializationProfile:
    """Frozen metadata governing one public corpus materialization."""

    profile_identity: str
    expected_system_id: str
    release_scope: str
    horizon_rule: str
    threshold_version: str
    published_artifacts: tuple[str, ...]

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.profile_identity,
                self.expected_system_id,
                self.release_scope,
                self.horizon_rule,
                self.threshold_version,
            )
        ):
            raise ValueError("materialization profile metadata is required")
        if not self.published_artifacts or not all(
            artifact.strip() for artifact in self.published_artifacts
        ):
            raise ValueError("published artifacts are required")


@dataclass(frozen=True)
class PublicCorpusSnapshot:
    system_id: str
    source_reference: str
    threshold_rule: str
    score_time: str
    window_end: str
    outcome_class: str
    censor_reason: str | None
    split: str
    change_group_id: str
    artifacts: tuple[str, ...]
    artifacts_complete: bool
    valid: bool
    uses_private_data: bool = False
    uses_privileged_telemetry: bool = False


@dataclass(frozen=True)
class PublicCorpusRecord:
    identity: str
    system_id: str
    source_reference: str
    threshold_rule: str
    score_time: str
    window_end: str
    outcome_class: str
    censor_reason: str | None
    split: str
    change_group_id: str
    artifact_count: int
    claim_scope: str = "public_corpus_evidence_only"


@dataclass(frozen=True)
class WithheldEvidenceRecord:
    input_identity: str
    reason: str
    constraint_class: str


@dataclass(frozen=True)
class PublicCorpusReport:
    materialization_identity: str
    profile_identity: str
    records: tuple[PublicCorpusRecord, ...]
    withheld: tuple[WithheldEvidenceRecord, ...]
    counts: dict[str, int]
    published_artifacts: tuple[str, ...]
    claim_scope: str = "public_corpus_evidence_only"


def _time(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must be RFC 3339 UTC")
    try:
        return datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as error:
        raise ValueError("timestamp must be RFC 3339 UTC") from error


def _identity_payload(
    item: PublicCorpusSnapshot, outcome: str, reason: str | None
) -> dict[str, object]:
    return {
        "system_id": item.system_id,
        "source_reference": item.source_reference,
        "threshold_rule": item.threshold_rule,
        "score_time": item.score_time,
        "window_end": item.window_end,
        "outcome_class": outcome,
        "censor_reason": reason,
        "split": item.split,
        "change_group_id": item.change_group_id,
        "artifact_count": len(item.artifacts),
    }


def _snapshot_identity(item: PublicCorpusSnapshot) -> str:
    payload = {
        "system_id": item.system_id,
        "source_reference": item.source_reference,
        "threshold_rule": item.threshold_rule,
        "score_time": item.score_time,
        "window_end": item.window_end,
        "outcome_class": item.outcome_class,
        "censor_reason": item.censor_reason,
        "split": item.split,
        "change_group_id": item.change_group_id,
        "artifacts": item.artifacts,
        "artifacts_complete": item.artifacts_complete,
        "valid": item.valid,
        "uses_private_data": item.uses_private_data,
        "uses_privileged_telemetry": item.uses_privileged_telemetry,
    }
    return content_hash(payload)


def normalize_public_corpus(
    snapshots: Iterable[PublicCorpusSnapshot],
) -> tuple[PublicCorpusRecord, ...]:
    """Normalize snapshots without network access or inferred positive outcomes."""
    records: list[PublicCorpusRecord] = []
    seen: set[tuple[str, str, str, str]] = set()
    ordered_snapshots = sorted(
        tuple(snapshots),
        key=lambda item: (
            _snapshot_identity(item)
            if isinstance(item, PublicCorpusSnapshot)
            else repr(item)
        ),
    )
    for item in ordered_snapshots:
        if not isinstance(item, PublicCorpusSnapshot):
            raise ValueError("snapshot is invalid")
        if (
            not item.system_id.strip()
            or not item.threshold_rule.strip()
            or not item.change_group_id.strip()
            or item.split not in _CANONICAL_SPLITS
            or item.outcome_class not in _ALLOWED_OUTCOMES
            or not item.source_reference.startswith("https://")
            or "@" in item.source_reference
            or "?token=" in item.source_reference
            or item.uses_private_data
            or item.uses_privileged_telemetry
            or not item.artifacts
            or len(set(item.artifacts)) != len(item.artifacts)
        ):
            raise ValueError("corpus evidence is not public and complete")
        score, end = _time(item.score_time), _time(item.window_end)
        if score >= end:
            raise ValueError("observation window must be ordered")
        if item.outcome_class == "censored" and not item.censor_reason:
            raise ValueError("censored observation requires reason")
        key = (item.system_id, item.source_reference, item.score_time, item.split)
        if key in seen:
            raise ValueError("corpus snapshots must be unique")

        if item.valid and item.artifacts_complete:
            outcome, reason = item.outcome_class, item.censor_reason
        elif not item.valid:
            outcome, reason = "censored", "public corpus input is invalid"
        else:
            outcome, reason = "censored", "public corpus artifacts are incomplete"

        payload = _identity_payload(item, outcome, reason)
        identity = content_hash(payload)
        records.append(PublicCorpusRecord(identity=identity, **payload))
        seen.add(key)

    return tuple(
        sorted(
            records,
            key=lambda record: (
                record.system_id,
                record.score_time,
                record.source_reference,
                record.split,
            ),
        )
    )


def materialize_public_corpus(
    profile: PublicCorpusMaterializationProfile,
    snapshots: Iterable[PublicCorpusSnapshot],
) -> PublicCorpusReport:
    """Build a deterministic evidence-only report with explicit withholding."""

    if not isinstance(profile, PublicCorpusMaterializationProfile):
        raise ValueError("materialization profile is invalid")

    included: list[PublicCorpusRecord] = []
    withheld: list[WithheldEvidenceRecord] = []
    seen: set[tuple[str, str, str, str]] = set()
    ordered_snapshots = sorted(
        tuple(snapshots),
        key=lambda item: (
            _snapshot_identity(item)
            if isinstance(item, PublicCorpusSnapshot)
            else repr(item)
        ),
    )
    for item in ordered_snapshots:
        input_identity = (
            _snapshot_identity(item)
            if isinstance(item, PublicCorpusSnapshot)
            else bytes_hash(repr(item).encode())
        )
        try:
            if not isinstance(item, PublicCorpusSnapshot):
                raise ValueError("snapshot is invalid")
            if item.system_id != profile.expected_system_id:
                raise ValueError("snapshot does not match expected system")
            if item.threshold_rule != profile.threshold_version:
                raise ValueError("snapshot does not match threshold version")
            key = (item.system_id, item.source_reference, item.score_time, item.split)
            if key in seen:
                raise ValueError("corpus snapshots must be unique")
            included.extend(normalize_public_corpus([item]))
            seen.add(key)
        except ValueError as error:
            message = str(error)
            constraint_class = (
                "profile_mismatch"
                if "match" in message
                else "integrity"
                if "invalid" in message or "unique" in message
                else "public_scope"
            )
            withheld.append(
                WithheldEvidenceRecord(input_identity, message, constraint_class)
            )

    records = tuple(sorted(included, key=lambda record: record.identity))
    withheld_records = tuple(sorted(withheld, key=lambda record: record.input_identity))
    counts = {
        outcome: sum(record.outcome_class == outcome for record in records)
        for outcome in _ALLOWED_OUTCOMES
    }
    payload = {
        "profile_identity": profile.profile_identity,
        "records": [record.__dict__ for record in records],
        "withheld": [record.__dict__ for record in withheld_records],
        "published_artifacts": profile.published_artifacts,
    }
    materialization_identity = content_hash(payload)
    return PublicCorpusReport(
        materialization_identity=materialization_identity,
        profile_identity=profile.profile_identity,
        records=records,
        withheld=withheld_records,
        counts=counts,
        published_artifacts=profile.published_artifacts,
    )


__all__ = [
    "PublicCorpusMaterializationProfile",
    "PublicCorpusReport",
    "PublicCorpusRecord",
    "PublicCorpusSnapshot",
    "WithheldEvidenceRecord",
    "materialize_public_corpus",
    "normalize_public_corpus",
]
