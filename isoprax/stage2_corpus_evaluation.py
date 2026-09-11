"""Claim-bounded corpus integrity and per-family evaluation for Stage 2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

from .admission import CorpusRow
from .commensurability import Attestation, OutcomeDefinition, check_commensurable
from .evaluation import check_calibration_conformance
from .identity import canonical_json, content_hash

CLAIM_BOUNDARY = (
    "Stage 2 corpus evaluation evidence only; this report does not establish "
    "Semantic or Full Conformance, pooled cross-family performance, causality, "
    "or generalization beyond the released corpus."
)


@dataclass(frozen=True)
class CorpusEvaluationProfile:
    candidate_id: str
    feasibility_report_identity: str
    predeclaration_artifact_hash: str
    corpus_artifact_hash: str
    change_definition: OutcomeDefinition
    operational_definition: OutcomeDefinition
    change_score_field: str
    operational_score_field: str
    horizon_rule: str
    threshold_version: str
    allowed_evidence_scope: str
    published_artifacts: tuple[str, ...]
    min_test_rows: int = 4
    min_test_positives: int = 2
    min_test_negatives: int = 2
    max_ece: float = 0.05
    attestation: Attestation | None = None

    def __post_init__(self) -> None:
        text_fields = (
            self.candidate_id,
            self.feasibility_report_identity,
            self.predeclaration_artifact_hash,
            self.corpus_artifact_hash,
            self.change_score_field,
            self.operational_score_field,
            self.horizon_rule,
            self.threshold_version,
            self.allowed_evidence_scope,
        )
        if any(
            not isinstance(value, str) or not value.strip() for value in text_fields
        ):
            raise ValueError("corpus evaluation metadata is required")
        if not self.published_artifacts or len(set(self.published_artifacts)) != len(
            self.published_artifacts
        ):
            raise ValueError("published artifacts must be non-empty and unique")
        if (
            min(self.min_test_rows, self.min_test_positives, self.min_test_negatives)
            < 1
        ):
            raise ValueError("evaluation minimums must be positive")
        if not 0.0 <= self.max_ece <= 1.0:
            raise ValueError("max_ece must be between 0 and 1")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "feasibility_report_identity": self.feasibility_report_identity,
            "predeclaration_artifact_hash": self.predeclaration_artifact_hash,
            "corpus_artifact_hash": self.corpus_artifact_hash,
            "change_definition": self.change_definition.to_dict(),
            "operational_definition": self.operational_definition.to_dict(),
            "change_score_field": self.change_score_field,
            "operational_score_field": self.operational_score_field,
            "horizon_rule": self.horizon_rule,
            "threshold_version": self.threshold_version,
            "allowed_evidence_scope": self.allowed_evidence_scope,
            "published_artifacts": self.published_artifacts,
            "min_test_rows": self.min_test_rows,
            "min_test_positives": self.min_test_positives,
            "min_test_negatives": self.min_test_negatives,
            "max_ece": self.max_ece,
            "attestation": self.attestation.__dict__ if self.attestation else None,
        }


@dataclass(frozen=True)
class CorpusEvaluationGate:
    gate_id: str
    status: str
    message: str
    observed: Any = None

    def __post_init__(self) -> None:
        if self.status not in {"pass", "inconclusive", "blocked"}:
            raise ValueError("corpus evaluation gate status is invalid")

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class CorpusEvaluationReport:
    report_identity: str
    profile_identity: str
    status: str
    counts: dict[str, int]
    family_reports: dict[str, dict[str, Any]]
    pooling: dict[str, Any]
    gates: tuple[CorpusEvaluationGate, ...]
    claim_boundary: str = CLAIM_BOUNDARY
    claim_scope: str = "stage2_corpus_evaluation_only"

    def __post_init__(self) -> None:
        if self.status not in {"qualified", "inconclusive", "blocked"}:
            raise ValueError("corpus evaluation status is invalid")
        if self.claim_boundary != CLAIM_BOUNDARY:
            raise ValueError("claim boundary is invalid")

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_identity": self.report_identity,
            "profile_identity": self.profile_identity,
            "status": self.status,
            "counts": self.counts,
            "family_reports": self.family_reports,
            "pooling": self.pooling,
            "gates": [gate.to_dict() for gate in self.gates],
            "claim_boundary": self.claim_boundary,
            "claim_scope": self.claim_scope,
        }


def _profile_identity(profile: CorpusEvaluationProfile) -> str:
    return content_hash(profile.identity_payload())


def _score(row: CorpusRow, field: str) -> float:
    if field not in row.prediction_fields:
        raise ValueError(f"missing predeclared score field '{field}'")
    value = row.prediction_fields[field]
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("score field must be numeric")
    score = float(value)
    if not 0.0 <= score <= 1.0:
        raise ValueError("score field must be in [0, 1]")
    observed_at = row.prediction_field_observed_at.get(field)
    if observed_at is None:
        raise ValueError("prediction field observation time is missing")
    if datetime.fromisoformat(observed_at) > datetime.fromisoformat(row.score_time):
        raise ValueError("prediction field is post-score-time")
    return score


def _outcome(row: CorpusRow) -> int | None:
    if row.outcome_class == "observed_positive":
        return 1
    if row.outcome_class == "observed_negative":
        return 0
    return None


def _counts(rows: tuple[CorpusRow, ...]) -> dict[str, int]:
    test = [row for row in rows if row.split == "test"]
    labeled = [row for row in test if _outcome(row) is not None]
    return {
        "selected": len(rows),
        "test_rows": len(test),
        "test_labeled": len(labeled),
        "positive": sum(_outcome(row) == 1 for row in labeled),
        "negative": sum(_outcome(row) == 0 for row in labeled),
        "censored": sum(_outcome(row) is None for row in rows),
        "build_failed": sum(not row.build_succeeded for row in rows),
        "deployment_failed": sum(not row.deployment_succeeded for row in rows),
        "monitoring_incomplete": sum(not row.monitoring_complete for row in rows),
        "withheld": 0,
        "excluded": 0,
    }


def _family_report(
    rows: tuple[CorpusRow, ...],
    field: str,
    profile: CorpusEvaluationProfile,
) -> dict[str, Any]:
    test = [row for row in rows if row.split == "test" and _outcome(row) is not None]
    scores = [_score(row, field) for row in test]
    outcomes = [_outcome(row) for row in test]
    assert all(outcome is not None for outcome in outcomes)
    evidence = check_calibration_conformance(
        scores,
        outcomes,
        min_events=profile.min_test_rows,
        max_ece=profile.max_ece,
    )
    enough_classes = (
        evidence.positive_events >= profile.min_test_positives
        and evidence.negative_events >= profile.min_test_negatives
    )
    qualified = evidence.passes and enough_classes
    reason = evidence.reason
    if not enough_classes:
        reason = (
            "minimum positive/negative outcome class counts are not met "
            f"({evidence.positive_events}/{profile.min_test_positives}, "
            f"{evidence.negative_events}/{profile.min_test_negatives})"
        )
    return {
        "status": "qualified" if qualified else "inconclusive",
        "metrics": {
            "ece": evidence.ece,
            "brier": evidence.brier,
            "auc": evidence.auc,
            "score_variance": evidence.score_variance,
        },
        "counts": {
            "test_labeled": evidence.n_events,
            "positive": evidence.positive_events,
            "negative": evidence.negative_events,
        },
        "reason": reason,
    }


def evaluate_stage2_corpus(
    rows: Iterable[CorpusRow], profile: CorpusEvaluationProfile
) -> CorpusEvaluationReport:
    """Evaluate one frozen corpus without pooling its family results."""
    ordered = tuple(sorted(rows, key=lambda row: row.row_id))
    if not ordered:
        raise ValueError("corpus rows are required")
    if len({row.row_id for row in ordered}) != len(ordered):
        raise ValueError("corpus rows must be unique")
    changes = [row.change_id for row in ordered]
    if len(set(changes)) != len(changes):
        raise ValueError("change appears in multiple rows")
    if any(row.system_id != profile.candidate_id for row in ordered):
        raise ValueError("corpus row system mismatches profile")
    if any(
        row.horizon_rule_used != profile.horizon_rule
        or row.threshold_version != profile.threshold_version
        for row in ordered
    ):
        raise ValueError("corpus row lane metadata mismatches profile")
    if any(not row.observation_id.strip() or not row.linkage_bases for row in ordered):
        raise ValueError("corpus row shared-observation lineage is missing")
    for row in ordered:
        _score(row, profile.change_score_field)
        _score(row, profile.operational_score_field)
    commensurability = check_commensurable(
        profile.change_definition,
        profile.operational_definition,
        attestation=profile.attestation,
    )
    counts = _counts(ordered)
    profile_id = _profile_identity(profile)
    pooling = {
        "status": "withheld" if commensurability.pooling_allowed else "blocked",
        "reason": (
            "cross-family pooling is withheld by claim boundary"
            if commensurability.pooling_allowed
            else f"incommensurable definitions: {commensurability.reason}"
        ),
        "level": commensurability.level,
    }
    if not commensurability.pooling_allowed:
        family_reports = {
            family: {
                "status": "blocked",
                "metrics": {},
                "counts": {},
                "reason": pooling["reason"],
            }
            for family in ("change", "operational")
        }
        gates = (
            CorpusEvaluationGate("commensurability", "blocked", pooling["reason"]),
        )
        status = "blocked"
    else:
        family_reports = {
            "change": _family_report(ordered, profile.change_score_field, profile),
            "operational": _family_report(
                ordered, profile.operational_score_field, profile
            ),
        }
        family_pass = all(
            item["status"] == "qualified" for item in family_reports.values()
        )
        gates = (
            CorpusEvaluationGate(
                "label_yield",
                "pass" if family_pass else "inconclusive",
                "both family evaluations meet declared label and score gates"
                if family_pass
                else "one or more family evaluations are inconclusive",
                counts["test_labeled"],
            ),
            CorpusEvaluationGate(
                "pooling",
                "pass",
                "cross-family pooling withheld even though definitions are commensurable",
            ),
        )
        status = "qualified" if family_pass else "inconclusive"
    payload = {
        "profile_identity": profile_id,
        "status": status,
        "counts": counts,
        "family_reports": family_reports,
        "pooling": pooling,
        "gates": [gate.to_dict() for gate in gates],
        "claim_boundary": CLAIM_BOUNDARY,
        "claim_scope": "stage2_corpus_evaluation_only",
    }
    return CorpusEvaluationReport(
        content_hash(payload),
        profile_id,
        status,
        counts,
        family_reports,
        pooling,
        gates,
    )


def validate_stage2_corpus_evaluation_report(
    report: CorpusEvaluationReport,
) -> None:
    expected = report.to_dict()
    actual = expected.pop("report_identity")
    if content_hash(expected) != actual:
        raise ValueError("report identity does not match canonical report")
    if any(
        field in canonical_json(report.to_dict())
        for field in ("change_score", "operational_score")
    ):
        raise ValueError("raw prediction scores must not be published")
