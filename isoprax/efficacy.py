"""Fail-closed, per-family efficacy evidence for optional JEPA backends."""

from __future__ import annotations

import math
from dataclasses import dataclass, fields
from numbers import Real
from types import MappingProxyType
from typing import Any, Iterable, Mapping

import numpy as np
from sklearn.metrics import roc_auc_score

from .eb_jepa import EBJEPATrainingReport
from .evaluation import brier_score, expected_calibration_error
from .identity import content_hash
from .jepa import EvidenceProvenance

CLAIM_BOUNDARY = (
    "Scoped per-family held-out efficacy evidence only; does not establish Semantic "
    "or Full Conformance, does not authorize cross-family pooling, and does not "
    "imply efficacy beyond the declared corpus, split, model, baseline, and thresholds."
)
_CLAIMABLE_MIN_TEST_ROWS = 800
_CLAIMABLE_MIN_POSITIVE_EVENTS = 50
_CLAIMABLE_MIN_NEGATIVE_EVENTS = 50


def _materialize(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        return (value,)
    try:
        return tuple(value)
    except TypeError:
        return (value,)


def _profile_payload(profile: "EfficacyEvaluationProfile") -> dict[str, Any]:
    return {
        field.name: (
            profile.provenance.to_dict()
            if field.name == "provenance" and profile.provenance is not None
            else getattr(profile, field.name)
        )
        for field in fields(profile)
    }


def _provenance_reasons(
    profile: "EfficacyEvaluationProfile",
    outcome_definition_ids: Iterable[str] | None = None,
) -> list[str]:
    if profile.evidence_class != "real_labeled":
        return [
            "evidence class is synthetic; real labeled held-out evidence is required"
        ]
    if profile.provenance is None:
        return ["real labeled evidence lacks a provenance artifact"]
    if not profile.provenance.verified:
        return ["real labeled evidence provenance is not externally verified"]
    payload = profile.provenance.payload
    reasons: list[str] = []
    if payload.get("corpus_identity") != profile.corpus_identity:
        reasons.append("provenance corpus identity does not match the profile")
    if payload.get("split_identity") != profile.split_identity:
        reasons.append("provenance split identity does not match the profile")
    if outcome_definition_ids is not None:
        declared = tuple(payload["outcome_definition_ids"])
        expected = tuple(outcome_definition_ids)
        if declared != expected:
            reasons.append(
                "provenance outcome definitions do not match the evaluated families"
            )
    return reasons


def _protected_floor_reasons(profile: "EfficacyEvaluationProfile") -> list[str]:
    if profile.evidence_class != "real_labeled":
        return []
    reasons: list[str] = []
    if profile.min_test_rows < _CLAIMABLE_MIN_TEST_ROWS:
        reasons.append("claimable evidence requires at least 800 test rows per family")
    if profile.min_positive_events < _CLAIMABLE_MIN_POSITIVE_EVENTS:
        reasons.append(
            "claimable evidence requires at least 50 positive events per family"
        )
    if profile.min_negative_events < _CLAIMABLE_MIN_NEGATIVE_EVENTS:
        reasons.append(
            "claimable evidence requires at least 50 negative events per family"
        )
    return reasons


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
    provenance: EvidenceProvenance | None = None

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
        if self.provenance is not None and not isinstance(
            self.provenance, EvidenceProvenance
        ):
            raise ValueError("provenance must be an EvidenceProvenance")
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
        return content_hash(_profile_payload(self))


@dataclass(frozen=True)
class EfficacyFamilyScores:
    """Candidate and baseline probabilities for one held-out family."""

    family: str
    outcome_definition_id: str
    test_row_ids: tuple[str, ...] | Iterable[str]
    outcomes: tuple[int, ...] | Iterable[int]
    candidate_scores: tuple[float, ...] | Iterable[float]
    baseline_scores: tuple[float, ...] | Iterable[float] = ()

    def __post_init__(self) -> None:
        for name in ("family", "outcome_definition_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        row_ids = _materialize(self.test_row_ids)
        outcomes = _materialize(self.outcomes)
        candidate = _materialize(self.candidate_scores)
        baseline = _materialize(self.baseline_scores)
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
    test_row_ids_digest: str = ""

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
            "test_row_ids_digest": self.test_row_ids_digest,
        }


def _passed_family_result_reasons(
    family: str,
    result: FamilyEfficacyResult,
    profile: EfficacyEvaluationProfile,
) -> list[str]:
    reasons: list[str] = []
    if (
        result.family != family
        or not isinstance(result.outcome_definition_id, str)
        or not result.outcome_definition_id.strip()
    ):
        reasons.append("family result identity is incomplete")
    if (
        not isinstance(result.test_row_ids_digest, str)
        or len(result.test_row_ids_digest) != 64
        or any(
            character not in "0123456789abcdef"
            for character in result.test_row_ids_digest
        )
    ):
        reasons.append("family test-row identity digest is missing or invalid")
    required_metrics = (
        "candidate_auc",
        "baseline_auc",
        "candidate_brier",
        "baseline_brier",
        "candidate_ece",
        "baseline_ece",
        "auc_gain",
    )
    metric_values: dict[str, float] = {}
    for name in required_metrics:
        value = result.metrics.get(name)
        if isinstance(value, bool) or not isinstance(value, Real):
            reasons.append(f"family metric {name} is missing or non-numeric")
            continue
        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            reasons.append(f"family metric {name} is missing or non-finite")
            continue
        metric_values[name] = numeric_value
    required_counts = ("test_rows", "positive_events", "negative_events")
    for name in required_counts:
        value = result.counts.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            reasons.append(f"family count {name} is invalid")
    if reasons:
        return reasons
    for name in (
        "candidate_auc",
        "baseline_auc",
        "candidate_brier",
        "baseline_brier",
        "candidate_ece",
        "baseline_ece",
    ):
        if not 0.0 <= metric_values[name] <= 1.0:
            reasons.append(f"family metric {name} is outside the [0, 1] domain")
    if not -1.0 <= metric_values["auc_gain"] <= 1.0:
        reasons.append("family metric auc_gain is outside the [-1, 1] domain")
    if result.counts["test_rows"] != (
        result.counts["positive_events"] + result.counts["negative_events"]
    ):
        reasons.append("family counts are inconsistent with test_rows")
    if reasons:
        return reasons
    if result.counts["test_rows"] < profile.min_test_rows:
        reasons.append("family result is below the declared test-row threshold")
    if result.counts["positive_events"] < profile.min_positive_events:
        reasons.append("family result is below the declared positive-event threshold")
    if result.counts["negative_events"] < profile.min_negative_events:
        reasons.append("family result is below the declared negative-event threshold")
    if metric_values["candidate_auc"] < profile.minimum_candidate_auc:
        reasons.append("family result candidate AUC is below the profile threshold")
    if metric_values["auc_gain"] < profile.minimum_auc_gain:
        reasons.append("family result AUC gain is below the profile threshold")
    if metric_values["candidate_ece"] > profile.max_candidate_ece:
        reasons.append("family result ECE exceeds the profile threshold")
    if metric_values["candidate_brier"] > (
        metric_values["baseline_brier"] + profile.max_brier_regression
    ):
        reasons.append("family result Brier score exceeds the baseline threshold")
    return reasons


def _report_identity_payload(
    *,
    status: str,
    profile: EfficacyEvaluationProfile,
    model_identity: str,
    training_report: EBJEPATrainingReport | None,
    training_report_identity: str,
    run_configuration_identity: str,
    run_configuration: Mapping[str, Any],
    claim_scope: str,
    family_results: Mapping[str, FamilyEfficacyResult],
    reasons: tuple[str, ...],
    claim_boundary: str,
) -> dict[str, Any]:
    return {
        "status": status,
        "profile": _profile_payload(profile),
        "model_identity": model_identity,
        "training_report": (
            training_report.to_dict() if training_report is not None else None
        ),
        "training_report_identity": training_report_identity,
        "run_configuration_identity": run_configuration_identity,
        "run_configuration": dict(run_configuration),
        "claim_scope": claim_scope,
        "family_results": {
            family: result.to_dict() for family, result in family_results.items()
        },
        "reasons": list(reasons),
        "claim_boundary": claim_boundary,
    }


@dataclass(frozen=True)
class EfficacyReport:
    status: str
    report_identity: str
    profile_identity: str
    profile: EfficacyEvaluationProfile
    model_identity: str
    training_report_identity: str
    run_configuration_identity: str
    run_configuration: Mapping[str, Any]
    claim_scope: str
    training_report: EBJEPATrainingReport | None
    family_results: Mapping[str, FamilyEfficacyResult]
    reasons: tuple[str, ...]
    pooled_score: None = None
    claim_boundary: str = CLAIM_BOUNDARY

    def __post_init__(self) -> None:
        if self.status not in {"not_claimable", "efficacy_supported"}:
            raise ValueError("efficacy report status is invalid")
        if self.pooled_score is not None:
            raise ValueError("cross-family pooled efficacy is not supported")
        if self.status == "not_claimable" and not self.reasons:
            raise ValueError("not_claimable reports must include failure reasons")
        if not isinstance(self.profile, EfficacyEvaluationProfile):
            raise ValueError("profile must be an EfficacyEvaluationProfile")
        if self.profile_identity != self.profile.identity:
            raise ValueError("profile_identity does not match the serialized profile")
        if not isinstance(self.model_identity, str) or not self.model_identity.strip():
            raise ValueError("model_identity is required")
        if self.training_report is not None and not isinstance(
            self.training_report, EBJEPATrainingReport
        ):
            raise ValueError("training_report must be an EBJEPATrainingReport")
        if self.status == "efficacy_supported" and self.training_report is None:
            raise ValueError("efficacy_supported requires a validated training report")
        if self.training_report is not None:
            if self.training_report.backend_identity != self.model_identity:
                raise ValueError(
                    "training report backend identity does not match the model"
                )
            expected_training_report_identity = content_hash(
                self.training_report.to_dict()
            )
            if self.training_report_identity != expected_training_report_identity:
                raise ValueError(
                    "training_report_identity does not match the serialized training report"
                )
        elif self.training_report_identity:
            raise ValueError("training_report_identity requires a training report")
        if not isinstance(self.run_configuration, Mapping):
            raise ValueError("run_configuration must be a mapping")
        run_configuration = dict(self.run_configuration)
        try:
            expected_run_configuration_identity = content_hash(run_configuration)
        except (TypeError, ValueError) as error:
            raise ValueError("run_configuration must be canonical JSON data") from error
        if self.run_configuration_identity != expected_run_configuration_identity:
            raise ValueError(
                "run_configuration_identity does not match the serialized configuration"
            )
        family_results = dict(self.family_results)
        if any(
            not isinstance(family, str) or not isinstance(result, FamilyEfficacyResult)
            for family, result in family_results.items()
        ):
            raise ValueError("family_results must map names to FamilyEfficacyResult")
        object.__setattr__(self, "family_results", MappingProxyType(family_results))
        object.__setattr__(
            self, "run_configuration", MappingProxyType(run_configuration)
        )
        required = set(self.profile.required_families)
        if self.status == "efficacy_supported":
            if not run_configuration:
                raise ValueError("efficacy_supported requires run_configuration")
            if run_configuration.get("backend_identity") != self.model_identity:
                raise ValueError(
                    "efficacy_supported requires run_configuration backend identity"
                )
            results = self.family_results
            outcome_ids = tuple(
                results[family].outcome_definition_id
                for family in self.profile.required_families
                if family in results
            )
            if _provenance_reasons(
                self.profile, outcome_ids
            ) or _protected_floor_reasons(self.profile):
                raise ValueError(
                    "efficacy_supported requires verified real-labeled claim evidence"
                )
            result_reasons = [
                reason
                for family, result in results.items()
                for reason in _passed_family_result_reasons(
                    family, result, self.profile
                )
            ]
            if (
                self.reasons
                or set(results) != required
                or result_reasons
                or any(
                    result.status != "passed" or result.reasons
                    for result in results.values()
                )
            ):
                raise ValueError(
                    "efficacy_supported requires every required family to pass without reasons"
                )
        expected_report_identity = content_hash(
            _report_identity_payload(
                status=self.status,
                profile=self.profile,
                model_identity=self.model_identity,
                training_report=self.training_report,
                training_report_identity=self.training_report_identity,
                run_configuration_identity=self.run_configuration_identity,
                run_configuration=run_configuration,
                claim_scope=self.claim_scope,
                family_results=self.family_results,
                reasons=self.reasons,
                claim_boundary=self.claim_boundary,
            )
        )
        if self.report_identity != expected_report_identity:
            raise ValueError("report_identity does not match the serialized report")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "report_identity": self.report_identity,
            "profile_identity": self.profile_identity,
            "profile": _profile_payload(self.profile),
            "model_identity": self.model_identity,
            "training_report": (
                self.training_report.to_dict()
                if self.training_report is not None
                else None
            ),
            "training_report_identity": self.training_report_identity,
            "run_configuration_identity": self.run_configuration_identity,
            "run_configuration": dict(self.run_configuration),
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
        values = _materialize(split_row_ids[split])
        if not values or any(
            not isinstance(value, str) or not value for value in values
        ):
            reasons.append(f"{split} split row ids must be non-empty strings")
        if all(isinstance(value, str) and value for value in values):
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
    row_ids = tuple(item.test_row_ids)
    raw_outcomes = tuple(item.outcomes)
    raw_candidate = tuple(item.candidate_scores)
    raw_baseline = tuple(item.baseline_scores)
    reasons: list[str] = []
    if not row_ids or any(not isinstance(value, str) or not value for value in row_ids):
        reasons.append("test_row_ids must be non-empty strings")
    elif len(set(row_ids)) != len(row_ids):
        reasons.append("test_row_ids must be unique")
    if (
        row_ids
        and all(isinstance(value, str) and value for value in row_ids)
        and not set(row_ids).issubset(test_ids)
    ):
        reasons.append(
            "family test row ids are not contained in the declared test split"
        )

    aligned = (
        len({len(row_ids), len(raw_outcomes), len(raw_candidate), len(raw_baseline)})
        == 1
    )
    if not aligned:
        reasons.append("family scores and row ids must be aligned")

    outcomes: np.ndarray | None = None
    if not raw_outcomes:
        reasons.append("outcomes are missing")
    else:
        try:
            numeric_outcomes = np.asarray(raw_outcomes, dtype=float)
        except (OverflowError, TypeError, ValueError):
            reasons.append("outcomes must be one-dimensional binary integer labels")
        else:
            if numeric_outcomes.ndim != 1:
                reasons.append("outcomes must be one-dimensional binary integer labels")
            elif (
                any(
                    isinstance(value, bool) or not isinstance(value, Real)
                    for value in raw_outcomes
                )
                or not np.isfinite(numeric_outcomes).all()
                or not np.isin(numeric_outcomes, (0.0, 1.0)).all()
            ):
                reasons.append("outcomes must be binary")
            else:
                outcomes = numeric_outcomes.astype(int)

    def _probabilities(values: tuple[Any, ...], name: str) -> np.ndarray | None:
        if not values:
            reasons.append(f"{name} scores are missing")
            return None
        try:
            array = np.asarray(values, dtype=float)
        except (OverflowError, TypeError, ValueError):
            reasons.append(f"{name} scores must be numeric probabilities")
            return None
        if array.ndim != 1:
            reasons.append(f"{name} scores must be one-dimensional")
            return None
        if not np.isfinite(array).all() or not (
            (0.0 <= array).all() and (array <= 1.0).all()
        ):
            reasons.append(f"{name} scores must be finite probabilities")
            return None
        return array

    candidate = _probabilities(raw_candidate, "candidate")
    baseline = _probabilities(raw_baseline, "baseline")
    positives = int(outcomes.sum()) if outcomes is not None else 0
    negatives = int(len(outcomes) - positives) if outcomes is not None else 0
    test_rows = len(raw_outcomes)
    if test_rows < profile.min_test_rows:
        reasons.append(
            f"insufficient test rows ({test_rows} < {profile.min_test_rows})"
        )
    if positives < profile.min_positive_events:
        reasons.append(
            f"insufficient positive events ({positives} < {profile.min_positive_events})"
        )
    if negatives < profile.min_negative_events:
        reasons.append(
            f"insufficient negative events ({negatives} < {profile.min_negative_events})"
        )
    if candidate is not None and np.var(candidate) <= 0.0:
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
    if not aligned or outcomes is None or candidate is None or baseline is None:
        reasons.append("metrics are unavailable because evidence is invalid")
    elif positives == 0 or negatives == 0:
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
        "test_rows": test_rows,
        "positive_events": positives,
        "negative_events": negatives,
    }
    try:
        row_ids_digest = (
            content_hash(row_ids)
            if row_ids and all(isinstance(value, str) and value for value in row_ids)
            else ""
        )
    except (TypeError, ValueError):
        row_ids_digest = ""
    return FamilyEfficacyResult(
        family=item.family,
        outcome_definition_id=item.outcome_definition_id,
        status="passed" if not reasons else "not_claimable",
        metrics=metrics,
        counts=counts,
        reasons=tuple(reasons),
        test_row_ids_digest=row_ids_digest,
    )


def evaluate_eb_jepa_efficacy(
    profile: EfficacyEvaluationProfile,
    *,
    split_row_ids: Mapping[str, Iterable[str]],
    family_scores: Iterable[EfficacyFamilyScores],
    model_identity: str,
    training_completed: bool = False,
    training_report: EBJEPATrainingReport | None = None,
    run_configuration: Mapping[str, Any] | None = None,
) -> EfficacyReport:
    """Evaluate held-out per-family evidence under an immutable profile."""
    if not isinstance(profile, EfficacyEvaluationProfile):
        raise ValueError("profile must be an EfficacyEvaluationProfile")
    if not isinstance(model_identity, str) or not model_identity.strip():
        raise ValueError("model_identity is required")
    blocking_reasons = _split_reasons(split_row_ids)
    if training_completed is not True:
        blocking_reasons.append("training_completed must be explicitly true")
    if not isinstance(training_report, EBJEPATrainingReport):
        blocking_reasons.append(
            "a validated EB-JEPA training report is required for efficacy evidence"
        )
        validated_training_report = None
        training_report_identity = ""
    else:
        validated_training_report = training_report
        training_report_identity = content_hash(training_report.to_dict())
        if training_report.backend_identity != model_identity:
            blocking_reasons.append(
                "training report backend identity does not match model_identity"
            )
            validated_training_report = None
            training_report_identity = ""

    if isinstance(run_configuration, Mapping):
        candidate_configuration = dict(run_configuration)
        try:
            run_configuration_identity = content_hash(candidate_configuration)
        except (TypeError, ValueError):
            candidate_configuration = {}
            run_configuration_identity = content_hash(candidate_configuration)
            blocking_reasons.append(
                "run_configuration must contain canonical JSON data"
            )
        if not candidate_configuration:
            blocking_reasons.append("run_configuration is required")
        elif candidate_configuration.get("backend_identity") != model_identity:
            blocking_reasons.append(
                "run_configuration backend_identity does not match model_identity"
            )
    else:
        candidate_configuration = {}
        run_configuration_identity = content_hash(candidate_configuration)
        blocking_reasons.append("run_configuration is required")

    test_values = (
        _materialize(split_row_ids.get("test", ()))
        if isinstance(split_row_ids, Mapping)
        else ()
    )
    test_ids = (
        set(test_values)
        if all(isinstance(value, str) and value for value in test_values)
        else set()
    )
    try:
        items = tuple(family_scores)
    except TypeError:
        items = ()
        blocking_reasons.append("family_scores must be an iterable")
    by_family: dict[str, EfficacyFamilyScores] = {}
    for item in items:
        if not isinstance(item, EfficacyFamilyScores):
            blocking_reasons.append("family_scores must contain EfficacyFamilyScores")
            continue
        if item.family in by_family:
            blocking_reasons.append(f"duplicate family evidence: {item.family}")
        by_family[item.family] = item
    for family in profile.required_families:
        if family not in by_family:
            blocking_reasons.append(f"missing required family evidence: {family}")
    global_reasons = list(blocking_reasons)
    provenance_reasons = _provenance_reasons(profile)
    global_reasons.extend(provenance_reasons)
    global_reasons.extend(_protected_floor_reasons(profile))
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
    if not provenance_reasons and family_results:
        global_reasons.extend(
            _provenance_reasons(
                profile,
                tuple(
                    family_results[family].outcome_definition_id
                    for family in profile.required_families
                    if family in family_results
                ),
            )
        )
    status = "efficacy_supported" if not global_reasons else "not_claimable"
    claim_scope = f"{model_identity}:{profile.corpus_identity}:{profile.split_identity}"
    claim_scope = f"{claim_scope}:{run_configuration_identity}:{training_report_identity or 'missing'}"
    identity_payload = _report_identity_payload(
        status=status,
        profile=profile,
        model_identity=model_identity,
        training_report=validated_training_report,
        training_report_identity=training_report_identity,
        run_configuration_identity=run_configuration_identity,
        run_configuration=candidate_configuration,
        claim_scope=claim_scope,
        family_results=family_results,
        reasons=tuple(global_reasons),
        claim_boundary=CLAIM_BOUNDARY,
    )
    return EfficacyReport(
        status=status,
        report_identity=content_hash(identity_payload),
        profile_identity=profile.identity,
        profile=profile,
        model_identity=model_identity,
        training_report_identity=training_report_identity,
        run_configuration_identity=run_configuration_identity,
        run_configuration=candidate_configuration,
        claim_scope=claim_scope,
        training_report=validated_training_report,
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
