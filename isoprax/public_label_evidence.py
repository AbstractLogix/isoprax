"""Offline, provenance-first public label evidence reduction."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .commensurability import OutcomeDefinition, check_commensurable


class PublicLabelStatus(str, Enum):
    REPRODUCED = "reproduced"
    BLOCKED = "blocked"
    INCONCLUSIVE = "inconclusive"


class PublicLabelComparisonStatus(str, Enum):
    DIRECT = "direct"
    BRIDGEABLE = "bridgeable"
    IRREDUCIBLE = "irreducible"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class PublicLabelSource:
    source_id: str
    version: str
    license: str
    retrieval_reference: str
    checksum: str = ""


@dataclass(frozen=True)
class PublicLabelProcedure:
    """Evaluation procedure metadata; unknown values are never inferred."""

    split_strategy: str = "unknown"
    split_reference: str = ""
    model_version: str = "unknown"
    adaptation_policy: str = "unknown"

    def __post_init__(self) -> None:
        strategy = self.split_strategy.strip().lower()
        if strategy not in {"temporal", "random", "unknown"}:
            raise ValueError("split_strategy must be temporal, random, or unknown")
        object.__setattr__(self, "split_strategy", strategy)
        if not self.model_version.strip():
            object.__setattr__(self, "model_version", "unknown")
        if not self.adaptation_policy.strip():
            object.__setattr__(self, "adaptation_policy", "unknown")


@dataclass(frozen=True)
class PublicLabelDefinition:
    """A supplied, published label definition and its evaluation metadata."""

    source: PublicLabelSource
    outcome_definition: OutcomeDefinition
    procedure: PublicLabelProcedure = PublicLabelProcedure()
    retained_observations: bool = False
    bridge_provenance: str = ""
    aligned_event_count: int = 0
    disagreement_count: int = 0
    available: bool = True
    source_identity_current: bool = True

    def __post_init__(self) -> None:
        if self.aligned_event_count < 0 or self.disagreement_count < 0:
            raise ValueError("event and disagreement counts must be non-negative")
        if not self.source.source_id.strip():
            raise ValueError("source_id is required")
        if not self.outcome_definition.id.strip():
            raise ValueError("outcome definition id is required")

    @property
    def status(self) -> PublicLabelStatus:
        if not self.available:
            return PublicLabelStatus.BLOCKED
        if not self.source.license.strip():
            return PublicLabelStatus.BLOCKED
        if not self.source_identity_current:
            return PublicLabelStatus.INCONCLUSIVE
        if (
            not self.source.version.strip()
            or not self.source.retrieval_reference.strip()
        ):
            return PublicLabelStatus.INCONCLUSIVE
        return PublicLabelStatus.REPRODUCED


@dataclass(frozen=True)
class PublicLabelComparison:
    left_source_id: str
    right_source_id: str
    status: PublicLabelComparisonStatus
    differing_fields: tuple[str, ...]
    reason: str
    pooling_permitted: bool = False


@dataclass(frozen=True)
class PublicLabelSemanticsReport:
    status: PublicLabelStatus
    sources: tuple[PublicLabelDefinition, ...]
    comparisons: tuple[PublicLabelComparison, ...]
    reasons: tuple[str, ...]
    claim_boundary: str = (
        "public label semantics evidence only; not Semantic/Full Conformance, "
        "predictive efficacy, or label interchangeability"
    )


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


def _comparison(
    left: PublicLabelDefinition, right: PublicLabelDefinition
) -> PublicLabelComparison:
    if left.status != PublicLabelStatus.REPRODUCED:
        return PublicLabelComparison(
            left.source.source_id,
            right.source.source_id,
            PublicLabelComparisonStatus.UNAVAILABLE,
            (),
            f"left source is {left.status.value}",
        )
    if right.status != PublicLabelStatus.REPRODUCED:
        return PublicLabelComparison(
            left.source.source_id,
            right.source.source_id,
            PublicLabelComparisonStatus.UNAVAILABLE,
            (),
            f"right source is {right.status.value}",
        )

    retained = (
        left.retained_observations
        and right.retained_observations
        and bool(left.bridge_provenance.strip())
        and bool(right.bridge_provenance.strip())
    )
    result = check_commensurable(
        left.outcome_definition,
        right.outcome_definition,
        retained_observations=retained,
    )
    if result.level == "direct":
        status = PublicLabelComparisonStatus.DIRECT
    elif result.level == "bridgeable":
        status = PublicLabelComparisonStatus.BRIDGEABLE
    else:
        status = PublicLabelComparisonStatus.IRREDUCIBLE
    reason = result.reason
    if result.level == "bridgeable" and not retained:
        reason = "bridge evidence is required before a window/threshold mismatch can be re-derived"
    return PublicLabelComparison(
        left.source.source_id,
        right.source.source_id,
        status,
        tuple(result.differing_fields),
        reason,
    )


def build_public_label_semantics_report(
    definitions: tuple[PublicLabelDefinition, ...] | list[PublicLabelDefinition],
) -> PublicLabelSemanticsReport:
    """Reduce supplied label records into deterministic evidence only."""

    ordered = tuple(sorted(definitions, key=lambda item: item.source.source_id))
    source_ids = [item.source.source_id for item in ordered]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("source identifiers must be unique")
    comparisons = tuple(
        _comparison(ordered[left], ordered[right])
        for left in range(len(ordered))
        for right in range(left + 1, len(ordered))
    )
    statuses = [item.status for item in ordered]
    reasons = tuple(
        f"{item.source.source_id}: {item.status.value}"
        for item in ordered
        if item.status != PublicLabelStatus.REPRODUCED
    )
    if any(status == PublicLabelStatus.BLOCKED for status in statuses) or any(
        item.status == PublicLabelComparisonStatus.UNAVAILABLE for item in comparisons
    ):
        report_status = PublicLabelStatus.BLOCKED
    elif any(status == PublicLabelStatus.INCONCLUSIVE for status in statuses):
        report_status = PublicLabelStatus.INCONCLUSIVE
    else:
        report_status = PublicLabelStatus.REPRODUCED
    return PublicLabelSemanticsReport(
        report_status,
        ordered,
        comparisons,
        reasons,
    )
