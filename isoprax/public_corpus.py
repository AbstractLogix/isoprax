"""Offline normalization of supplied public corpus materialization snapshots."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

_CANONICAL_SPLITS = ("train", "calibration_fit", "calibration_gate", "test")
_ALLOWED_OUTCOMES = ("observed_positive", "observed_negative", "censored")


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


def normalize_public_corpus(
    snapshots: Iterable[PublicCorpusSnapshot],
) -> tuple[PublicCorpusRecord, ...]:
    """Normalize snapshots without network access or inferred positive outcomes."""
    records: list[PublicCorpusRecord] = []
    seen: set[tuple[str, str, str, str]] = set()
    for item in snapshots:
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
        identity = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
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


__all__ = [
    "PublicCorpusRecord",
    "PublicCorpusSnapshot",
    "normalize_public_corpus",
]
