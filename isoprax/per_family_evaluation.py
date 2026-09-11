"""Deterministic Stage 1 per-family evaluation from admitted corpus rows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from .admission import (
    AdmissionProfile,
    AdmissionReport,
    CorpusRow,
    evaluate_admission,
)
from .commensurability import OutcomeDefinition
from .evaluation import (
    brier_score,
    check_calibration_conformance,
    expected_calibration_error,
)
from .identity import content_hash

_ALLOWED_METRICS = ("brier_score", "ece", "positive_rate")
_ALLOWED_STATUSES = {"evaluation_evidence", "blocked", "inconclusive"}
_CLAIM_BOUNDARY = (
    "Per-family Stage 1 evaluation evidence only; does not establish Semantic or "
    "Full Conformance, does not authorize cross-family pooling, and does not imply "
    "model efficacy beyond observed scoped evidence."
)


@dataclass(frozen=True)
class PerFamilyEvaluationProfile:
    family: str
    outcome_definition: OutcomeDefinition
    score_field: str
    predeclared_threshold_version: str
    predeclared_metrics: tuple[str, ...] = _ALLOWED_METRICS

    def __post_init__(self) -> None:
        required = (
            self.family,
            self.score_field,
            self.predeclared_threshold_version,
            self.outcome_definition.id,
        )
        if not all(isinstance(value, str) and value.strip() for value in required):
            raise ValueError("per-family evaluation profile metadata is required")
        if (
            not self.predeclared_metrics
            or len(set(self.predeclared_metrics)) != len(self.predeclared_metrics)
            or any(
                metric not in _ALLOWED_METRICS for metric in self.predeclared_metrics
            )
        ):
            raise ValueError("predeclared metrics must be non-empty and canonical")


@dataclass(frozen=True)
class UnavailableEvaluationEvidence:
    category: str
    reason: str


@dataclass(frozen=True)
class PerFamilyEvaluationReport:
    evaluation_identity: str
    status: str
    family: str
    outcome_definition_id: str
    declarable_class: str
    metrics: Mapping[str, float]
    calibration: Mapping[str, Any]
    counts: Mapping[str, int]
    uncertainty: Mapping[str, float]
    unavailable_evidence: tuple[UnavailableEvaluationEvidence, ...]
    claim_boundary: str = _CLAIM_BOUNDARY
    claim_scope: str = "stage1_per_family_evaluation_only"

    def __post_init__(self) -> None:
        if self.status not in _ALLOWED_STATUSES:
            raise ValueError("evaluation status is invalid")
        for name in ("metrics", "calibration", "counts", "uncertainty"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation_identity": self.evaluation_identity,
            "status": self.status,
            "family": self.family,
            "outcome_definition_id": self.outcome_definition_id,
            "declarable_class": self.declarable_class,
            "metrics": dict(self.metrics),
            "calibration": dict(self.calibration),
            "counts": dict(self.counts),
            "uncertainty": dict(self.uncertainty),
            "unavailable_evidence": [
                item.__dict__ for item in self.unavailable_evidence
            ],
            "claim_boundary": self.claim_boundary,
            "claim_scope": self.claim_scope,
        }


def _row_by_id(rows: Iterable[CorpusRow]) -> dict[str, CorpusRow]:
    out: dict[str, CorpusRow] = {}
    for row in rows:
        if row.row_id in out:
            raise ValueError("evaluation rows must be unique")
        out[row.row_id] = row
    return out


def _score(row: CorpusRow, score_field: str) -> float:
    if score_field not in row.prediction_fields:
        raise ValueError(f"missing predeclared score field '{score_field}'")
    value = row.prediction_fields[score_field]
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("score field must be numeric")
    score = float(value)
    if score < 0.0 or score > 1.0:
        raise ValueError("score field must be in [0, 1]")
    return score


def _observed_outcome_value(row: CorpusRow) -> int | None:
    if row.outcome_class == "observed_positive":
        return 1
    if row.outcome_class == "observed_negative":
        return 0
    return None


def _test_counts(rows: tuple[CorpusRow, ...]) -> dict[str, int]:
    test_rows = [row for row in rows if row.split == "test"]
    observed = [row for row in test_rows if _observed_outcome_value(row) is not None]
    return {
        "rows": len(rows),
        "test_rows": len(test_rows),
        "test_observed": len(observed),
        "censored": len(test_rows) - len(observed),
    }


def _identity_payload(
    profile: PerFamilyEvaluationProfile,
    corpus_digest: str,
    **fields: object,
) -> dict[str, object]:
    return {
        "family": profile.family,
        "outcome_definition_id": profile.outcome_definition.id,
        "score_field": profile.score_field,
        "predeclared_threshold_version": profile.predeclared_threshold_version,
        "predeclared_metrics": list(profile.predeclared_metrics),
        "corpus_digest": corpus_digest,
        "claim_boundary": _CLAIM_BOUNDARY,
        "claim_scope": "stage1_per_family_evaluation_only",
        **fields,
    }


def _wilson_interval(
    successes: int, total: int, z: float = 1.96
) -> tuple[float, float]:
    p = successes / total
    denom = 1.0 + (z * z / total)
    center = (p + (z * z) / (2 * total)) / denom
    spread = (z / denom) * sqrt((p * (1 - p) / total) + (z * z) / (4 * total * total))
    return max(0.0, center - spread), min(1.0, center + spread)


def _split_checked_rows(
    rows: tuple[CorpusRow, ...],
    row_by_id: dict[str, CorpusRow],
    admission_profile: AdmissionProfile,
) -> tuple[list[CorpusRow], list[CorpusRow], list[CorpusRow]]:
    evidence = admission_profile.calibration_evidence
    if evidence is None:
        return [], [], [row for row in rows if row.split == "test"]
    for row_ids in (evidence.fitted_row_ids, evidence.gated_row_ids):
        if len(set(row_ids)) != len(row_ids):
            raise ValueError("calibration evidence row ids must be unique")
    try:
        fit_rows = [row_by_id[row_id] for row_id in evidence.fitted_row_ids]
        gate_rows = [row_by_id[row_id] for row_id in evidence.gated_row_ids]
    except KeyError as error:
        raise ValueError("calibration evidence references unknown rows") from error
    if any(row.split != "calibration_fit" for row in fit_rows):
        raise ValueError("calibration fit evidence must reference calibration_fit rows")
    if any(row.split != "calibration_gate" for row in gate_rows):
        raise ValueError(
            "calibration gate evidence must reference calibration_gate rows"
        )
    test_rows = [row for row in rows if row.split == "test"]
    return fit_rows, gate_rows, test_rows


def evaluate_per_family(
    rows: Iterable[CorpusRow],
    admission_profile: AdmissionProfile,
    admission_report: AdmissionReport,
    profile: PerFamilyEvaluationProfile,
) -> PerFamilyEvaluationReport:
    """Evaluate one admitted corpus for one family under predeclared constraints."""
    ordered_rows = tuple(sorted(rows, key=lambda row: row.row_id))
    if not ordered_rows:
        raise ValueError("evaluation rows are required")
    if not admission_profile.horizon_frozen or not admission_profile.thresholds_frozen:
        raise ValueError("post-hoc thresholds or horizon are forbidden")
    if admission_profile.predeclaration_evidence is None:
        raise ValueError("predeclaration evidence is required")
    row_by_id = _row_by_id(ordered_rows)
    corpus_digest = content_hash([asdict(row) for row in ordered_rows])
    if not admission_report.admissible:
        blocked = (
            UnavailableEvaluationEvidence("admission_report", "admission did not pass"),
        )
        blocked_counts = _test_counts(ordered_rows)
        payload = _identity_payload(
            profile,
            corpus_digest,
            status="blocked",
            counts=blocked_counts,
            unavailable_evidence=[item.__dict__ for item in blocked],
        )
        return PerFamilyEvaluationReport(
            evaluation_identity=content_hash(payload),
            status="blocked",
            family=profile.family,
            outcome_definition_id=profile.outcome_definition.id,
            declarable_class="Blocked admission evidence; no conformance class assigned",
            metrics={},
            calibration={},
            counts=blocked_counts,
            uncertainty={},
            unavailable_evidence=blocked,
        )

    for row in ordered_rows:
        if row.threshold_version != profile.predeclared_threshold_version:
            raise ValueError("row threshold version mismatches predeclared threshold")
        _score(row, profile.score_field)

    fit_rows, gate_rows, test_rows = _split_checked_rows(
        ordered_rows, row_by_id, admission_profile
    )
    if evaluate_admission(list(ordered_rows), admission_profile) != admission_report:
        raise ValueError("admission report does not match these rows and profile")

    unavailable: list[UnavailableEvaluationEvidence] = []
    if not fit_rows:
        unavailable.append(
            UnavailableEvaluationEvidence(
                "calibration_fit_rows", "calibration fit evidence is missing"
            )
        )
    if not gate_rows:
        unavailable.append(
            UnavailableEvaluationEvidence(
                "calibration_gate_rows", "calibration gate evidence is missing"
            )
        )
    if not test_rows:
        unavailable.append(
            UnavailableEvaluationEvidence("test_rows", "test split rows are missing")
        )

    gate_scores: list[float] = []
    gate_outcomes: list[int] = []
    for row in gate_rows:
        observed = _observed_outcome_value(row)
        if observed is None:
            continue
        gate_scores.append(_score(row, profile.score_field))
        gate_outcomes.append(observed)

    test_scores: list[float] = []
    test_outcomes: list[int] = []
    for row in test_rows:
        observed = _observed_outcome_value(row)
        if observed is None:
            continue
        test_scores.append(_score(row, profile.score_field))
        test_outcomes.append(observed)

    if not test_outcomes:
        unavailable.append(
            UnavailableEvaluationEvidence(
                "test_labeled_outcomes", "test split has no observed outcomes"
            )
        )

    metrics: dict[str, float] = {}
    if test_outcomes:
        available_metrics = {
            "brier_score": brier_score(test_scores, test_outcomes),
            "ece": expected_calibration_error(test_scores, test_outcomes),
            "positive_rate": float(sum(test_outcomes) / len(test_outcomes)),
        }
        metrics = {
            name: float(available_metrics[name]) for name in profile.predeclared_metrics
        }

    if gate_outcomes:
        cal = check_calibration_conformance(gate_scores, gate_outcomes)
        calibration = {
            "status": cal.as_declaration(),
            "passes": cal.passes,
            "ece": float(cal.ece),
            "brier": float(cal.brier),
            "n_events": cal.n_events,
            "reason": cal.reason,
        }
        if not cal.passes:
            unavailable.append(
                UnavailableEvaluationEvidence("calibration_conformance", cal.reason)
            )
    else:
        calibration = {
            "status": "uncalibrated",
            "passes": False,
            "ece": 1.0,
            "brier": 1.0,
            "n_events": 0,
            "reason": "no calibration gate outcomes available",
        }
        unavailable.append(
            UnavailableEvaluationEvidence(
                "calibration_diagnostics", "calibration gate outcomes are missing"
            )
        )

    uncertainty: dict[str, float] = {}
    if test_outcomes:
        lower, upper = _wilson_interval(sum(test_outcomes), len(test_outcomes))
        uncertainty = {
            "positive_rate_ci_low": float(lower),
            "positive_rate_ci_high": float(upper),
        }

    status = "inconclusive" if unavailable else "evaluation_evidence"
    counts = _test_counts(ordered_rows)
    payload = _identity_payload(
        profile,
        corpus_digest,
        status=status,
        metrics=metrics,
        calibration=calibration,
        counts=counts,
        uncertainty=uncertainty,
        unavailable_evidence=[item.__dict__ for item in unavailable],
    )
    return PerFamilyEvaluationReport(
        evaluation_identity=content_hash(payload),
        status=status,
        family=profile.family,
        outcome_definition_id=profile.outcome_definition.id,
        declarable_class=(
            "Stage 1 per-family evaluation evidence only; "
            "Cross-Family Conformance (Structural) unchanged"
        ),
        metrics=metrics,
        calibration=calibration,
        counts=counts,
        uncertainty=uncertainty,
        unavailable_evidence=tuple(
            sorted(unavailable, key=lambda item: (item.category, item.reason))
        ),
    )


__all__ = [
    "PerFamilyEvaluationProfile",
    "PerFamilyEvaluationReport",
    "UnavailableEvaluationEvidence",
    "evaluate_per_family",
]
