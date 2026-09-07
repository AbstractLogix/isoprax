"""Offline, provenance-first public label evidence reduction."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PublicLabelStatus(str, Enum):
    REPRODUCED = "reproduced"
    BLOCKED = "blocked"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class PublicLabelSource:
    source_id: str
    version: str
    license: str
    retrieval_reference: str
    checksum: str = ""


@dataclass(frozen=True)
class PublicLabelEvidenceManifest:
    sources: tuple[PublicLabelSource, ...]
    left_definition: str
    right_definition: str
    aligned_event_ids: tuple[str, ...]
    disagreement_count: int
    sources_available: bool = True
    licenses_verified: bool = True
    source_identities_current: bool = True


@dataclass(frozen=True)
class PublicLabelEvidenceRecord:
    status: PublicLabelStatus
    source_ids: tuple[str, ...]
    aligned_event_count: int
    disagreement_count: int
    reason: str
    claim_boundary: str = (
        "public label evidence is not Semantic/Full Conformance or predictive efficacy"
    )


def reduce_public_label_evidence(
    manifest: PublicLabelEvidenceManifest,
) -> PublicLabelEvidenceRecord:
    source_ids = tuple(sorted(source.source_id for source in manifest.sources))
    if not manifest.sources_available:
        return PublicLabelEvidenceRecord(
            PublicLabelStatus.BLOCKED,
            source_ids,
            len(manifest.aligned_event_ids),
            manifest.disagreement_count,
            "recorded public sources are unavailable",
        )
    if not manifest.licenses_verified:
        return PublicLabelEvidenceRecord(
            PublicLabelStatus.BLOCKED,
            source_ids,
            len(manifest.aligned_event_ids),
            manifest.disagreement_count,
            "source licensing is not verified",
        )
    if not manifest.source_identities_current:
        return PublicLabelEvidenceRecord(
            PublicLabelStatus.INCONCLUSIVE,
            source_ids,
            len(manifest.aligned_event_ids),
            manifest.disagreement_count,
            "source identity changed after manifest creation",
        )
    if not source_ids or not manifest.left_definition or not manifest.right_definition:
        return PublicLabelEvidenceRecord(
            PublicLabelStatus.INCONCLUSIVE,
            source_ids,
            len(manifest.aligned_event_ids),
            manifest.disagreement_count,
            "source and both published label definitions are required",
        )
    return PublicLabelEvidenceRecord(
        PublicLabelStatus.REPRODUCED,
        source_ids,
        len(manifest.aligned_event_ids),
        manifest.disagreement_count,
        "manifested public label comparison is reproducible",
    )
