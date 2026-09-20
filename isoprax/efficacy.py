"""Fail-closed, per-family efficacy evidence for optional JEPA backends."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping

import numpy as np
from sklearn.metrics import roc_auc_score

from .evaluation import brier_score, expected_calibration_error
from .identity import content_hash

CLAIM_BOUNDARY = (
    "Scoped per-family held-out efficacy evidence only; does not establish Semantic "
    "or Full Conformance, does not authorize cross-family pooling, and does not "
    "imply efficacy beyond the declared corpus, split, model, baseline, and thresholds."
)


@dataclass(frozen=True)
class EfficacyEvaluationProfile:
    """Predeclared gates applied before an efficacy status can be reported."""

    corpus_identity: str
    split_identity: str
    baseline_identity: str
    threshold_version: str
    min_test_rows: int = 800
    min_positive_events: int = 50
    min_negative_events: int = 50
    minimum_auc_gain: float = 0.0
    minimum_candidate_auc: float = 0.5
    max_candidate_ece: float = 0.05
    max_brier_regression: float = 0.0
    required_families: tuple[str, ...] = ("change", "operational")
    evidence_class: str = "synthetic"

    def __post_init__(self) -> None:
        for name in (
            "corpus_identity",
            "split_identity",
            "baseline_identity",
            "threshold_version",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        for name in (
            "min_test_rows",
            "min_positive_events",
            "min_negative_events",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        for name in (
            "minimum_auc_gain",
            "minimum_candidate_auc",
            "max_candidate_ece",
            "max_brier_regression",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise ValueError(f"{name} must be numeric")
            if not math.isfinite(float(value)) or float(value) < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")
        if self.minimum_candidate_auc > 1.0 or self.max_candidate_ece > 1.0:
            raise ValueError("probability thresholds must be at most 1")
        if self.evidence_class not in {"synthetic", "real_labeled"}:
            raise ValueError("evidence_class must be synthetic or real_labeled")
        families = tuple(self.required_families)
        if not families or len(set(families)) != len(families):
            raise ValueError("required_families must be non-empty and unique")
        if any(
            not isinstance(family, str) or not family.strip() for family in families
        ):
            raise ValueError("required_families must contain names")
        object.__setattr__(self, "required_families", families)

    @property
    def identity(self) -> str:
        return content_hash(asdict(self))


@dataclass(frozen=True)
class EfficacyFamilyScores:
    """Candidate and baseline probabilities for one held-out family."""

    family: str
    outcome_definition_id: str
    test_row_ids: tuple[str, ...]
    outcomes: tuple[int, ...]
    candidate_scores: tuple[float, ...]
    baseline_scores: tuple[float, ...]

    def __post_init__(self) -> None:
        for name in ("family", "outcome_definition_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        row_ids = tuple(self.test_row_ids)
        outcomes = tuple(self.outcomes)
        candidate = tuple(float(value) for value in self.candidate_scores)
        baseline = tuple(float(value) for value in self.baseline_scores)
        if not row_ids or len(set(row_ids)) != len(row_ids):
            raise ValueError("test_row_ids must be non-empty and unique")
        if len({len(outcomes), len(candidate), len(baseline), len(row_ids)}) != 1:
            raise ValueError("family scores and row ids must be aligned")
        if any(value not in (0, 1) for value in outcomes):
            raise ValueError("outcomes must be binary")
        if any(
            not math.isfinite(value) or not 0.0 <= value <= 1.0
            for value in (*candidate, *baseline)
        ):
            raise ValueError(
                "candidate and baseline scores must be finite probabilities"
            )
        object.__setattr__(self, "test_row_ids", row_ids)
        object.__setattr__(self, "outcomes", outcomes)
        object.__setattr__(self, "candidate_scores", candidate)
        object.__setattr__(self, "baseline_scores", baseline)


@dataclass(frozen=True)
class FamilyEfficacyResult:
    family: str
    outcome_definition_id: str
    status: str
    metrics: Mapping[str, float | None]
    counts: Mapping[str, int]
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in {"passed", "not_claimable"}:
            raise ValueError("family efficacy status is invalid")
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))
        object.__setattr__(self, "counts", MappingProxyType(dict(self.counts)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "outcome_definition_id": self.outcome_definition_id,
            "status": self.status,
            "metrics": dict(self.metrics),
            "counts": dict(self.counts),
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class EfficacyReport:
    status: str
    report_identity: str
    profile_identity: str
    profile: EfficacyEvaluationProfile
    model_identity: str
    claim_scope: str
    family_results: Mapping[str, FamilyEfficacyResult]
    reasons: tuple[str, ...]
    pooled_score: None = None
    claim_boundary: str = CLAIM_BOUNDARY

    def __post_init__(self) -> None:
        if self.status not in {"not_claimable", "efficacy_supported"}:
            raise ValueError("efficacy report status is invalid")
        if self.pooled_score is not None:
            raise ValueError("cross-family pooled efficacy is not supported")
        if not isinstance(self.profile, EfficacyEvaluationProfile):
            raise ValueError("profile must be an EfficacyEvaluationProfile")
        if self.profile_identity != self.profile.identity:
            raise ValueError("profile_identity does not match the serialized profile")
        object.__setattr__(
            self, "family_results", MappingProxyType(dict(self.family_results))
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "report_identity": self.report_identity,
            "profile_identity": self.profile_identity,
            "profile": asdict(self.profile),
            "model_identity": self.model_identity,
            "claim_scope": self.claim_scope,
            "family_results": {
                family: result.to_dict()
                for family, result in self.family_results.items()
            },
            "reasons": list(self.reasons),
            "pooled_score": None,
            "claim_boundary": self.claim_boundary,
        }


def _split_reasons(split_row_ids: Mapping[str, Iterable[str]]) -> list[str]:
    required = ("train", "calibration", "test")
    reasons: list[str] = []
    if not isinstance(split_row_ids, Mapping):
        return ["split_row_ids must be a mapping"]
    sets: dict[str, set[str]] = {}
    for split in required:
        if split not in split_row_ids:
            reasons.append(f"missing {split} split row ids")
            continue
        values = tuple(split_row_ids[split])
        if not values or any(
            not isinstance(value, str) or not value for value in values
        ):
            reasons.append(f"{split} split row ids must be non-empty strings")
        if len(set(values)) != len(values):
            reasons.append(f"{split} split row ids are duplicated")
        sets[split] = set(values)
    for left, right in (
        ("train", "calibration"),
        ("train", "test"),
        ("calibration", "test"),
    ):
        if left in sets and right in sets and sets[left] & sets[right]:
            reasons.append(f"split row ids overlap between {left} and {right}")
    return reasons


def _family_result(
    item: EfficacyFamilyScores,
    profile: EfficacyEvaluationProfile,
    test_ids: set[str],
) -> FamilyEfficacyResult:
    candidate = np.asarray(item.candidate_scores, dtype=float)
    baseline = np.asarray(item.baseline_scores, dtype=float)
    outcomes = np.asarray(item.outcomes, dtype=int)
    reasons: list[str] = []
    if not set(item.test_row_ids).issubset(test_ids):
        reasons.append(
            "family test row ids are not contained in the declared test split"
        )
    positives = int(outcomes.sum())
    negatives = int(len(outcomes) - positives)
    if len(outcomes) < profile.min_test_rows:
        reasons.append(
            f"insufficient test rows ({len(outcomes)} < {profile.min_test_rows})"
        )
    if positives < profile.min_positive_events:
        reasons.append(
            f"insufficient positive events ({positives} < {profile.min_positive_events})"
        )
    if negatives < profile.min_negative_events:
        reasons.append(
            f"insufficient negative events ({negatives} < {profile.min_negative_events})"
        )
    if np.var(candidate) <= 0.0:
        reasons.append("candidate scores are constant")
    metrics: dict[str, float | None] = {
        "candidate_auc": None,
        "baseline_auc": None,
        "candidate_brier": None,
        "baseline_brier": None,
        "candidate_ece": None,
        "baseline_ece": None,
        "auc_gain": None,
    }
    if positives == 0 or negatives == 0:
        reasons.append("test outcomes contain only one class; auc is unavailable")
    else:
        candidate_auc = float(roc_auc_score(outcomes, candidate))
        baseline_auc = float(roc_auc_score(outcomes, baseline))
        candidate_brier = brier_score(candidate.tolist(), outcomes.tolist())
        baseline_brier = brier_score(baseline.tolist(), outcomes.tolist())
        candidate_ece = expected_calibration_error(candidate, outcomes)
        baseline_ece = expected_calibration_error(baseline, outcomes)
        auc_gain = candidate_auc - baseline_auc
        metrics.update(
            candidate_auc=candidate_auc,
            baseline_auc=baseline_auc,
            candidate_brier=candidate_brier,
            baseline_brier=baseline_brier,
            candidate_ece=candidate_ece,
            baseline_ece=baseline_ece,
            auc_gain=auc_gain,
        )
        if candidate_auc < profile.minimum_candidate_auc:
            reasons.append(
                f"candidate auc {candidate_auc:.4f} is below "
                f"{profile.minimum_candidate_auc:.4f}"
            )
        if auc_gain < profile.minimum_auc_gain:
            reasons.append(
                f"auc gain {auc_gain:.4f} is below {profile.minimum_auc_gain:.4f}"
            )
        if candidate_ece > profile.max_candidate_ece:
            reasons.append(
                f"candidate ece {candidate_ece:.4f} exceeds "
                f"{profile.max_candidate_ece:.4f}"
            )
        if candidate_brier > baseline_brier + profile.max_brier_regression:
            reasons.append(
                "candidate brier is worse than the predeclared baseline gate"
            )
    counts = {
        "test_rows": len(outcomes),
        "positive_events": positives,
        "negative_events": negatives,
    }
    return FamilyEfficacyResult(
        family=item.family,
        outcome_definition_id=item.outcome_definition_id,
        status="passed" if not reasons else "not_claimable",
        metrics=metrics,
        counts=counts,
        reasons=tuple(reasons),
    )


def evaluate_eb_jepa_efficacy(
    profile: EfficacyEvaluationProfile,
    *,
    split_row_ids: Mapping[str, Iterable[str]],
    family_scores: Iterable[EfficacyFamilyScores],
    model_identity: str,
    training_completed: bool = True,
) -> EfficacyReport:
    """Evaluate held-out per-family evidence under an immutable profile."""
    if not isinstance(profile, EfficacyEvaluationProfile):
        raise ValueError("profile must be an EfficacyEvaluationProfile")
    if not isinstance(model_identity, str) or not model_identity.strip():
        raise ValueError("model_identity is required")
    blocking_reasons = _split_reasons(split_row_ids)
    if not training_completed:
        blocking_reasons.append(
            "training run is incomplete; efficacy evidence is unavailable"
        )
    test_ids = (
        set(split_row_ids.get("test", ()))
        if isinstance(split_row_ids, Mapping)
        else set()
    )
    items = tuple(family_scores)
    by_family: dict[str, EfficacyFamilyScores] = {}
    for item in items:
        if not isinstance(item, EfficacyFamilyScores):
            raise ValueError("family_scores must contain EfficacyFamilyScores")
        if item.family in by_family:
            blocking_reasons.append(f"duplicate family evidence: {item.family}")
        by_family[item.family] = item
    for family in profile.required_families:
        if family not in by_family:
            blocking_reasons.append(f"missing required family evidence: {family}")
    global_reasons = list(blocking_reasons)
    if profile.evidence_class != "real_labeled":
        global_reasons.append(
            "evidence class is synthetic; real labeled held-out evidence is required"
        )
    if blocking_reasons:
        family_results = {
            family: FamilyEfficacyResult(
                family=family,
                outcome_definition_id=by_family[family].outcome_definition_id
                if family in by_family
                else "",
                status="not_claimable",
                metrics={},
                counts={},
                reasons=("global evidence gate failed",),
            )
            for family in profile.required_families
            if family in by_family
        }
    else:
        family_results = {
            family: _family_result(by_family[family], profile, test_ids)
            for family in profile.required_families
        }
    for result in family_results.values():
        global_reasons.extend(f"{result.family}: {reason}" for reason in result.reasons)
    status = "efficacy_supported" if not global_reasons else "not_claimable"
    claim_scope = f"{model_identity}:{profile.corpus_identity}:{profile.split_identity}"
    identity_payload = {
        "status": status,
        "profile": asdict(profile),
        "model_identity": model_identity,
        "claim_scope": claim_scope,
        "family_results": {
            family: result.to_dict() for family, result in family_results.items()
        },
        "reasons": global_reasons,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    return EfficacyReport(
        status=status,
        report_identity=content_hash(identity_payload),
        profile_identity=profile.identity,
        profile=profile,
        model_identity=model_identity,
        claim_scope=claim_scope,
        family_results=family_results,
        reasons=tuple(global_reasons),
    )


__all__ = [
    "CLAIM_BOUNDARY",
    "EfficacyEvaluationProfile",
    "EfficacyFamilyScores",
    "EfficacyReport",
    "FamilyEfficacyResult",
    "evaluate_eb_jepa_efficacy",
]
