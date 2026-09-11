"""Offline normalization of supplied public operational observations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .identity import content_hash


@dataclass(frozen=True)
class PublicObservationSnapshot:
    system_id: str
    source_reference: str
    threshold_rule: str
    score_time: str
    window_end: str
    artifacts: tuple[str, ...]
    artifacts_complete: bool
    valid: bool
    uses_private_data: bool = False
    uses_privileged_telemetry: bool = False


@dataclass(frozen=True)
class PublicObservationRecord:
    identity: str
    system_id: str
    source_reference: str
    threshold_rule: str
    score_time: str
    window_end: str
    outcome_class: str
    censor_reason: str | None
    artifact_count: int
    claim_scope: str = "public_observation_evidence_only"


def _time(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must be RFC 3339 UTC")
    try:
        return datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as error:
        raise ValueError("timestamp must be RFC 3339 UTC") from error


def normalize_public_observations(
    snapshots: Iterable[PublicObservationSnapshot],
) -> tuple[PublicObservationRecord, ...]:
    """Normalize snapshots without network access or inferred negative outcomes."""
    records = []
    seen: set[tuple[str, str]] = set()
    for item in snapshots:
        if not isinstance(item, PublicObservationSnapshot):
            raise ValueError("snapshot is invalid")
        if (
            not item.system_id.strip()
            or not item.threshold_rule.strip()
            or not item.source_reference.startswith("https://")
            or "@" in item.source_reference
            or "?token=" in item.source_reference
            or item.uses_private_data
            or item.uses_privileged_telemetry
            or not item.artifacts
            or len(set(item.artifacts)) != len(item.artifacts)
        ):
            raise ValueError("observation evidence is not public and complete")
        score, end = _time(item.score_time), _time(item.window_end)
        if score >= end:
            raise ValueError("observation window must be ordered")
        key = (item.system_id, item.score_time)
        if key in seen:
            raise ValueError("observation snapshots must be unique")
        if item.valid and item.artifacts_complete:
            outcome, reason = "observed", None
        elif not item.valid:
            outcome, reason = "censored", "public observation is invalid"
        else:
            outcome, reason = "censored", "public observation artifacts are incomplete"
        payload = {
            "system_id": item.system_id,
            "source_reference": item.source_reference,
            "threshold_rule": item.threshold_rule,
            "score_time": item.score_time,
            "window_end": item.window_end,
            "outcome_class": outcome,
            "censor_reason": reason,
            "artifact_count": len(item.artifacts),
        }
        records.append(
            PublicObservationRecord(
                content_hash(payload),
                **payload,
            )
        )
        seen.add(key)
    return tuple(
        sorted(records, key=lambda record: (record.system_id, record.score_time))
    )
