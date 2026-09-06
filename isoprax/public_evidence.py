"""Offline normalization of explicitly supplied public VCS/CI evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


@dataclass(frozen=True)
class PublicEvidenceSnapshot:
    system_id: str
    revision: str
    source_reference: str
    ci_reference: str | None
    ci_revision: str | None
    observed_at: str
    uses_private_data: bool = False
    uses_privileged_telemetry: bool = False


@dataclass(frozen=True)
class PublicEvidenceRecord:
    identity: str
    system_id: str
    revision: str
    source_reference: str
    ci_reference: str | None
    observed_at: str
    available: bool
    unavailable_reason: str | None
    claim_scope: str = "candidate_build_preparation_evidence_only"


def _valid_reference(value: str) -> bool:
    return value.startswith("https://") and "@" not in value and "?token=" not in value


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def normalize_public_evidence(
    snapshots: Iterable[PublicEvidenceSnapshot],
) -> tuple[PublicEvidenceRecord, ...]:
    """Normalize public snapshots without I/O or qualification claims."""
    records: list[PublicEvidenceRecord] = []
    seen: set[tuple[str, str]] = set()
    for item in snapshots:
        if not isinstance(item, PublicEvidenceSnapshot):
            raise ValueError("snapshot is invalid")
        key = (item.system_id, item.revision)
        if not item.system_id.strip() or len(item.revision) != 40 or key in seen:
            raise ValueError("system and immutable revision must be unique")
        if not _valid_reference(item.source_reference):
            raise ValueError("source reference is not public and safe")
        if item.uses_private_data or item.uses_privileged_telemetry:
            raise ValueError("private or privileged evidence is forbidden")
        try:
            datetime.fromisoformat(item.observed_at.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("observed timestamp is invalid") from error
        if item.ci_reference is not None:
            if (
                not _valid_reference(item.ci_reference)
                or item.ci_revision != item.revision
            ):
                raise ValueError("CI evidence does not match immutable revision")
            available, reason = True, None
        else:
            available, reason = False, "public CI evidence is unavailable"
        payload = {
            "system_id": item.system_id,
            "revision": item.revision,
            "source_reference": item.source_reference,
            "ci_reference": item.ci_reference,
            "observed_at": item.observed_at,
            "available": available,
            "unavailable_reason": reason,
        }
        records.append(
            PublicEvidenceRecord(
                hashlib.sha256(_canonical(payload).encode()).hexdigest(), **payload
            )
        )
        seen.add(key)
    return tuple(
        sorted(records, key=lambda record: (record.system_id, record.revision))
    )
