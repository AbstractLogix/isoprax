"""Typed evidence gates for declared Isoprax outcome families.

Marker types provide static consistency for definitions known to application
code. Every evidence factory also binds its token to the concrete definition
IDs, which remains authoritative for dynamically loaded definitions.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from numbers import Integral
from typing import Generic, Protocol, TypeVar

from .commensurability import (
    Attestation,
    OutcomeDefinition,
    PoolableCommensurabilityResult,
    require_commensurable,
)
from .identity import content_hash

LeftDefinition = TypeVar("LeftDefinition")
RightDefinition = TypeVar("RightDefinition")
Definition = TypeVar("Definition")


class CalibrationQualification(Protocol):
    """Minimal checked result shape returned by calibration evaluation."""

    @property
    def passes(self) -> bool: ...

    @property
    def reason(self) -> str: ...


@dataclass(frozen=True)
class _EvidenceSeal:
    pass


_EVIDENCE_SEAL = _EvidenceSeal()


@dataclass(frozen=True)
class CalibrationEvidence(Generic[Definition]):
    """A passing calibration result bound to one declared outcome family."""

    _seal: _EvidenceSeal = field(repr=False, compare=False)
    definition_id: str
    qualification: CalibrationQualification
    sample_digest: str

    def __post_init__(self) -> None:
        if self._seal is not _EVIDENCE_SEAL:
            raise TypeError("CalibrationEvidence must be created by its validator")
        if not self.sample_digest:
            raise ValueError("calibration evidence requires a sample digest")


@dataclass(frozen=True)
class CommensurabilityEvidence(Generic[LeftDefinition, RightDefinition]):
    """A poolable relationship bound to ordered left and right definitions."""

    _seal: _EvidenceSeal = field(repr=False, compare=False)
    left_definition_id: str
    right_definition_id: str
    result: PoolableCommensurabilityResult

    def __post_init__(self) -> None:
        if self._seal is not _EVIDENCE_SEAL:
            raise TypeError("CommensurabilityEvidence must be created by its validator")
        if not self.result.pooling_allowed:
            raise ValueError("commensurability evidence must permit pooling")
        if (
            self.result.left_id != self.left_definition_id
            or self.result.right_id != self.right_definition_id
        ):
            raise ValueError("commensurability evidence IDs do not match its result")


@dataclass(frozen=True)
class PooledComparisonAuthorization(Generic[LeftDefinition, RightDefinition]):
    """Proof token required by typed pooled-evaluation operations."""

    _seal: _EvidenceSeal = field(repr=False, compare=False)
    left_definition_id: str
    right_definition_id: str
    left_sample_digest: str
    right_sample_digest: str

    def __post_init__(self) -> None:
        if self._seal is not _EVIDENCE_SEAL:
            raise TypeError(
                "PooledComparisonAuthorization must be issued by its validator"
            )


def establish_commensurability(
    left: OutcomeDefinition,
    right: OutcomeDefinition,
    *,
    left_tag: type[LeftDefinition],
    right_tag: type[RightDefinition],
    attestation: Attestation | None = None,
    retained_observations: bool = False,
) -> CommensurabilityEvidence[LeftDefinition, RightDefinition]:
    """Return typed pooling evidence only when the existing policy permits it."""
    del left_tag, right_tag  # The marker classes exist only in the static type.
    result = require_commensurable(
        left,
        right,
        attestation=attestation,
        retained_observations=retained_observations,
    )
    return CommensurabilityEvidence(
        _EVIDENCE_SEAL,
        left.id,
        right.id,
        result,
    )


def establish_calibration(
    definition: OutcomeDefinition,
    scores: Sequence[float],
    outcomes: Sequence[int],
    *,
    tag: type[Definition],
    min_events: int = 500,
    n_bins: int = 10,
    max_ece: float = 0.05,
) -> CalibrationEvidence[Definition]:
    """Evaluate and bind successful calibration evidence to a definition."""
    del tag  # The marker class exists only in the static type.
    from .evaluation import check_calibration_conformance

    normalized_scores = tuple(float(score) for score in scores)
    normalized_outcomes = _normalize_binary_outcomes(outcomes)
    result = check_calibration_conformance(
        normalized_scores,
        normalized_outcomes,
        min_events=min_events,
        n_bins=n_bins,
        max_ece=max_ece,
    )
    if not result.passes:
        raise ValueError(result.reason)
    return CalibrationEvidence(
        _EVIDENCE_SEAL,
        definition.id,
        result,
        calibration_sample_digest(normalized_scores, normalized_outcomes),
    )


def calibration_sample_digest(scores: Sequence[float], outcomes: Sequence[int]) -> str:
    """Hash a normalized calibration sample for later evidence binding."""
    normalized_outcomes = _normalize_binary_outcomes(outcomes)
    return content_hash(
        {
            "scores": [float(score) for score in scores],
            "outcomes": list(normalized_outcomes),
        }
    )


def _normalize_binary_outcomes(outcomes: Sequence[int]) -> tuple[int, ...]:
    normalized: list[int] = []
    for outcome in outcomes:
        if not isinstance(outcome, Integral) or outcome not in (0, 1):
            raise ValueError("outcomes must be binary integers 0 or 1")
        normalized.append(int(outcome))
    return tuple(normalized)


def authorize_pooled_comparison(
    commensurability: CommensurabilityEvidence[LeftDefinition, RightDefinition],
    left_calibration: CalibrationEvidence[LeftDefinition],
    right_calibration: CalibrationEvidence[RightDefinition],
) -> PooledComparisonAuthorization[LeftDefinition, RightDefinition]:
    """Check concrete ID binding after the generic types checked the flow."""
    if commensurability.left_definition_id != left_calibration.definition_id:
        raise ValueError("left calibration evidence targets a different definition")
    if commensurability.right_definition_id != right_calibration.definition_id:
        raise ValueError("right calibration evidence targets a different definition")
    return PooledComparisonAuthorization(
        _EVIDENCE_SEAL,
        commensurability.left_definition_id,
        commensurability.right_definition_id,
        left_calibration.sample_digest,
        right_calibration.sample_digest,
    )
