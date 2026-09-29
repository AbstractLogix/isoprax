"""Typed evidence gates for declared Isoprax outcome families.

Marker types provide static consistency for definitions known to application
code. Every evidence factory also binds its token to the concrete definition
IDs, which remains authoritative for dynamically loaded definitions.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from numbers import Integral, Real
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

    @property
    def n_events(self) -> int: ...

    @property
    def n_bins(self) -> int: ...

    @property
    def max_ece(self) -> float: ...


@dataclass(frozen=True)
class _EvidenceSeal:
    pass


_EVIDENCE_SEAL = _EvidenceSeal()


@dataclass(frozen=True)
class CalibrationPolicy:
    """The complete calibration policy used to qualify pooled evidence."""

    min_events: int = 500
    n_bins: int = 10
    max_ece: float = 0.05

    def __post_init__(self) -> None:
        if isinstance(self.min_events, bool) or not isinstance(
            self.min_events, Integral
        ):
            raise TypeError("calibration policy min_events must be an integer")
        if self.min_events < 0:
            raise ValueError("calibration policy min_events must not be negative")
        if isinstance(self.n_bins, bool) or not isinstance(self.n_bins, Integral):
            raise TypeError("calibration policy n_bins must be an integer")
        if self.n_bins < 1:
            raise ValueError("calibration policy n_bins must be positive")
        if isinstance(self.max_ece, bool) or not isinstance(self.max_ece, Real):
            raise TypeError("calibration policy max_ece must be a finite number")
        max_ece = float(self.max_ece)
        if not math.isfinite(max_ece) or not 0.0 <= max_ece <= 1.0:
            raise ValueError("calibration policy max_ece must be finite and in [0, 1]")
        object.__setattr__(self, "min_events", int(self.min_events))
        object.__setattr__(self, "n_bins", int(self.n_bins))
        object.__setattr__(self, "max_ece", max_ece)

    @property
    def digest(self) -> str:
        return content_hash(
            {
                "kind": "isoprax.calibration-policy",
                "version": 1,
                "min_events": self.min_events,
                "n_bins": self.n_bins,
                "max_ece": self.max_ece,
            }
        )


@dataclass(frozen=True)
class CalibrationEvidence(Generic[Definition]):
    """A passing calibration result bound to definition, sample, and policy."""

    _seal: _EvidenceSeal = field(repr=False, compare=False)
    definition_id: str
    definition_content_digest: str
    qualification: CalibrationQualification
    sample_digest: str
    calibration_policy: CalibrationPolicy

    def __post_init__(self) -> None:
        if self._seal is not _EVIDENCE_SEAL:
            raise TypeError("CalibrationEvidence must be created by its validator")
        if not self.definition_id.strip():
            raise ValueError("calibration evidence requires a definition ID")
        if not self.definition_content_digest:
            raise ValueError(
                "calibration evidence requires a definition-content digest"
            )
        if not self.sample_digest:
            raise ValueError("calibration evidence requires a sample digest")
        if not self.qualification.passes:
            raise ValueError("calibration evidence requires a passing qualification")
        if self.qualification.n_events < self.calibration_policy.min_events:
            raise ValueError("calibration qualification does not meet its event policy")
        if (
            self.qualification.n_bins != self.calibration_policy.n_bins
            or self.qualification.max_ece != self.calibration_policy.max_ece
        ):
            raise ValueError("calibration qualification does not match its policy")

    @property
    def calibration_policy_digest(self) -> str:
        return self.calibration_policy.digest


@dataclass(frozen=True)
class CommensurabilityEvidence(Generic[LeftDefinition, RightDefinition]):
    """A poolable relationship bound to ordered left and right definitions."""

    _seal: _EvidenceSeal = field(repr=False, compare=False)
    left_definition_id: str
    right_definition_id: str
    left_definition_content_digest: str
    right_definition_content_digest: str
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
        if not self.left_definition_content_digest or not (
            self.right_definition_content_digest
        ):
            raise ValueError(
                "commensurability evidence requires definition-content digests"
            )


@dataclass(frozen=True)
class PooledComparisonAuthorization(Generic[LeftDefinition, RightDefinition]):
    """Proof token required by typed pooled-evaluation operations."""

    _seal: _EvidenceSeal = field(repr=False, compare=False)
    left_definition_id: str
    right_definition_id: str
    left_definition_content_digest: str
    right_definition_content_digest: str
    left_sample_digest: str
    right_sample_digest: str
    calibration_policy: CalibrationPolicy

    def __post_init__(self) -> None:
        if self._seal is not _EVIDENCE_SEAL:
            raise TypeError(
                "PooledComparisonAuthorization must be issued by its validator"
            )
        if not self.left_definition_content_digest or not (
            self.right_definition_content_digest
        ):
            raise ValueError("pooled authorization requires definition-content digests")
        if not self.left_sample_digest or not self.right_sample_digest:
            raise ValueError("pooled authorization requires calibration sample digests")

    @property
    def calibration_policy_digest(self) -> str:
        return self.calibration_policy.digest


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
        _definition_content_digest(left),
        _definition_content_digest(right),
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

    policy = CalibrationPolicy(min_events, n_bins, max_ece)
    normalized_scores = tuple(float(score) for score in scores)
    normalized_outcomes = _normalize_binary_outcomes(outcomes)
    result = check_calibration_conformance(
        normalized_scores,
        normalized_outcomes,
        min_events=policy.min_events,
        n_bins=policy.n_bins,
        max_ece=policy.max_ece,
    )
    if not result.passes:
        raise ValueError(result.reason)
    return CalibrationEvidence(
        _EVIDENCE_SEAL,
        definition.id,
        _definition_content_digest(definition),
        result,
        calibration_sample_digest(normalized_scores, normalized_outcomes),
        policy,
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
    """Check concrete definition, sample, and policy binding at runtime."""
    if commensurability.left_definition_id != left_calibration.definition_id:
        raise ValueError("left calibration evidence targets a different definition")
    if commensurability.right_definition_id != right_calibration.definition_id:
        raise ValueError("right calibration evidence targets a different definition")
    if (
        commensurability.left_definition_content_digest
        != left_calibration.definition_content_digest
    ):
        raise ValueError(
            "left calibration evidence targets different definition content"
        )
    if (
        commensurability.right_definition_content_digest
        != right_calibration.definition_content_digest
    ):
        raise ValueError(
            "right calibration evidence targets different definition content"
        )
    if left_calibration.calibration_policy != right_calibration.calibration_policy:
        raise ValueError("left and right calibration policies must match")
    return PooledComparisonAuthorization(
        _EVIDENCE_SEAL,
        commensurability.left_definition_id,
        commensurability.right_definition_id,
        commensurability.left_definition_content_digest,
        commensurability.right_definition_content_digest,
        left_calibration.sample_digest,
        right_calibration.sample_digest,
        left_calibration.calibration_policy,
    )


def _definition_content_digest(definition: OutcomeDefinition) -> str:
    """Hash the normalized semantics compared by the commensurability policy."""
    return content_hash(
        {
            "kind": "isoprax.outcome-definition-content",
            "version": 1,
            "comparison_key": definition.comparison_key(),
        }
    )
