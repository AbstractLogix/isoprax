"""Deterministic feasibility evidence for a bounded Stage 2 replay pilot."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping

from .commensurability import (
    Attestation,
    CommensurabilityResult,
    OutcomeDefinition,
    check_commensurable,
)
from .replay_capture import ReplayCaptureRecord

PILOT_STATUSES = frozenset({"feasible", "inconclusive", "blocked"})
TERMINAL_STATUSES = frozenset(
    {"observed_positive", "observed_negative", "censored", "blocked-before-compilation"}
)
CLAIM_BOUNDARY = (
    "Stage 2 replay feasibility evidence only; this report does not establish "
    "Semantic or Full Conformance, pooled cross-family performance, model "
    "efficacy, or full-corpus adequacy."
)


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("prediction timestamp must be a string")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("prediction timestamp is invalid") from error


def _required_text(values: Mapping[str, str]) -> None:
    if any(
        not isinstance(value, str) or not value.strip() for value in values.values()
    ):
        raise ValueError("pilot metadata is required")


@dataclass(frozen=True)
class ReplayPilotProfile:
    """Predeclared, immutable configuration for one bounded replay pilot."""

    candidate_id: str
    system_id: str
    service_id: str
    selected_commits: tuple[str, ...]
    workload_reference: str
    change_definition: OutcomeDefinition
    operational_definition: OutcomeDefinition
    horizon_rule: str
    threshold_version: str
    capture_schema_version: str
    allowed_evidence_scope: str
    published_artifacts: tuple[str, ...]
    predeclaration_artifact_hash: str
    external_anchor_reference: str
    predeclaration_commit: str
    corpus_data_commits: tuple[str, ...]
    predeclaration_is_ancestor: bool
    allowed_prediction_fields: frozenset[str] = frozenset()
    forbidden_prediction_fields: frozenset[str] = frozenset()
    min_complete_records: int = 1
    require_both_outcomes: bool = True
    min_observation_rate: float = 1.0
    require_repeatability: bool = False
    attestation: Attestation | None = None

    def __post_init__(self) -> None:
        _required_text(
            {
                "candidate_id": self.candidate_id,
                "system_id": self.system_id,
                "service_id": self.service_id,
                "workload_reference": self.workload_reference,
                "horizon_rule": self.horizon_rule,
                "threshold_version": self.threshold_version,
                "capture_schema_version": self.capture_schema_version,
                "allowed_evidence_scope": self.allowed_evidence_scope,
                "predeclaration_artifact_hash": self.predeclaration_artifact_hash,
                "external_anchor_reference": self.external_anchor_reference,
                "predeclaration_commit": self.predeclaration_commit,
            }
        )
        if not self.selected_commits or any(
            not isinstance(commit, str) or not commit.strip()
            for commit in self.selected_commits
        ):
            raise ValueError("selected commits must be non-empty")
        if len(set(self.selected_commits)) != len(self.selected_commits):
            raise ValueError("selected commits must be unique")
        if not self.published_artifacts or len(set(self.published_artifacts)) != len(
            self.published_artifacts
        ):
            raise ValueError("published artifacts must be non-empty and unique")
        if not self.corpus_data_commits or len(set(self.corpus_data_commits)) != len(
            self.corpus_data_commits
        ):
            raise ValueError("corpus data commits must be non-empty and unique")
        if not self.predeclaration_is_ancestor:
            raise ValueError(
                "predeclaration must be an ancestor of corpus data commits"
            )
        if self.min_complete_records < 1:
            raise ValueError("min_complete_records must be positive")
        if not 0.0 <= self.min_observation_rate <= 1.0:
            raise ValueError("min_observation_rate must be between 0 and 1")
        if not isinstance(self.change_definition, OutcomeDefinition) or not isinstance(
            self.operational_definition, OutcomeDefinition
        ):
            raise ValueError("outcome definitions are required")
        result = self.commensurability()
        if result.level not in {"direct", "attested"}:
            raise ValueError(
                "pilot requires direct or attested shared outcome semantics: "
                f"{result.reason}"
            )

    def commensurability(self) -> CommensurabilityResult:
        return check_commensurable(
            self.change_definition,
            self.operational_definition,
            attestation=self.attestation,
            retained_observations=True,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "system_id": self.system_id,
            "service_id": self.service_id,
            "selected_commits": self.selected_commits,
            "workload_reference": self.workload_reference,
            "change_definition": self.change_definition.to_dict(),
            "operational_definition": self.operational_definition.to_dict(),
            "horizon_rule": self.horizon_rule,
            "threshold_version": self.threshold_version,
            "capture_schema_version": self.capture_schema_version,
            "allowed_evidence_scope": self.allowed_evidence_scope,
            "published_artifacts": self.published_artifacts,
            "predeclaration_artifact_hash": self.predeclaration_artifact_hash,
            "external_anchor_reference": self.external_anchor_reference,
            "predeclaration_commit": self.predeclaration_commit,
            "corpus_data_commits": self.corpus_data_commits,
            "predeclaration_is_ancestor": self.predeclaration_is_ancestor,
            "allowed_prediction_fields": sorted(self.allowed_prediction_fields),
            "forbidden_prediction_fields": sorted(self.forbidden_prediction_fields),
            "min_complete_records": self.min_complete_records,
            "require_both_outcomes": self.require_both_outcomes,
            "min_observation_rate": self.min_observation_rate,
            "require_repeatability": self.require_repeatability,
            "attestation": None
            if self.attestation is None
            else self.attestation.__dict__,
        }

    @property
    def profile_identity(self) -> str:
        return _hash(self.to_dict())


@dataclass(frozen=True)
class ReplayTerminalRecord:
    """One immutable terminal result for one selected revision."""

    commit: str
    lane_identity: str
    run_identity: str
    terminal_status: str
    stage: str
    reason: str | None
    capture: ReplayCaptureRecord
    artifact_manifest: tuple[dict[str, Any], ...] = ()
    change_label: str | None = None
    operational_label: str | None = None
    shared_observation_identity: str = ""
    prediction_field_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (
            not self.commit.strip()
            or not self.lane_identity.strip()
            or not self.run_identity.strip()
        ):
            raise ValueError("terminal identity is required")
        if self.terminal_status not in TERMINAL_STATUSES:
            raise ValueError("terminal status is invalid")
        if self.terminal_status in {"censored", "blocked-before-compilation"} and not (
            self.reason and self.reason.strip()
        ):
            raise ValueError("censored and blocked terminal records require a reason")
        if not isinstance(self.capture, ReplayCaptureRecord):
            raise ValueError("terminal capture is invalid")
        if self.terminal_status in {"observed_positive", "observed_negative"} and (
            not self.change_label
            or not self.operational_label
            or self.change_label != self.operational_label
            or not self.shared_observation_identity
        ):
            raise ValueError("complete terminal records require shared family labels")

    def summary(self) -> dict[str, Any]:
        return {
            "commit": self.commit,
            "lane_identity": self.lane_identity,
            "run_identity": self.run_identity,
            "terminal_status": self.terminal_status,
            "stage": self.stage,
            "reason": self.reason,
            "artifact_manifest": self.artifact_manifest,
            "change_label": self.change_label,
            "operational_label": self.operational_label,
            "shared_observation_identity": self.shared_observation_identity,
            "prediction_field_names": self.prediction_field_names,
        }


@dataclass(frozen=True)
class RepeatabilityCheck:
    lane_identity: str
    run_identities: tuple[str, ...]
    outcome_agreement: bool
    label_agreement: bool
    artifact_agreement: bool
    discrepancies: tuple[str, ...]
    status: str

    def __post_init__(self) -> None:
        if self.status not in {"pass", "fail", "inconclusive"}:
            raise ValueError("repeatability status is invalid")

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class FeasibilityGate:
    gate_id: str
    status: str
    message: str
    observed: float | int | bool | None = None

    def __post_init__(self) -> None:
        if self.status not in {"pass", "inconclusive", "fail"}:
            raise ValueError("gate status is invalid")

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class FeasibilityReport:
    report_identity: str
    profile_identity: str
    status: str
    counts: dict[str, int]
    rates: dict[str, float | None]
    temporal_coverage: dict[str, Any]
    throughput: dict[str, float]
    repeatability: tuple[RepeatabilityCheck, ...]
    release_readiness: dict[str, Any]
    gates: tuple[FeasibilityGate, ...]
    extrapolation: dict[str, Any]
    terminal_summaries: tuple[dict[str, Any], ...]
    claim_boundary: str = CLAIM_BOUNDARY
    claim_scope: str = "stage2_replay_feasibility_only"

    def __post_init__(self) -> None:
        if self.status not in PILOT_STATUSES:
            raise ValueError("pilot status is invalid")
        if self.claim_boundary != CLAIM_BOUNDARY:
            raise ValueError("claim boundary is invalid")

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_identity": self.report_identity,
            "profile_identity": self.profile_identity,
            "status": self.status,
            "counts": self.counts,
            "rates": self.rates,
            "temporal_coverage": self.temporal_coverage,
            "throughput": self.throughput,
            "repeatability": [item.to_dict() for item in self.repeatability],
            "release_readiness": self.release_readiness,
            "gates": [gate.to_dict() for gate in self.gates],
            "extrapolation": self.extrapolation,
            "terminal_summaries": self.terminal_summaries,
            "claim_boundary": self.claim_boundary,
            "claim_scope": self.claim_scope,
        }


def _artifact_manifest(capture: ReplayCaptureRecord) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "path": artifact.path,
            "state": artifact.state,
            "sha256": artifact.sha256,
            "byte_count": artifact.byte_count,
        }
        for artifact in sorted(capture.artifacts, key=lambda item: item.path)
    )


def _terminal_status(capture: ReplayCaptureRecord) -> tuple[str, str]:
    if capture.outcome_class in {"observed_positive", "observed_negative"}:
        return capture.outcome_class, "observation"
    reason = capture.censor_reason or "capture did not complete"
    if capture.outcome_class == "blocked-before-compilation" or (
        capture.deployment is None
        and ("build" in reason.lower() or "execution" in reason.lower())
    ):
        return "blocked-before-compilation", "build_or_execution"
    return "censored", "observation"


def _validate_lane(profile: ReplayPilotProfile, capture: ReplayCaptureRecord) -> None:
    lane = capture.lane
    expected = {
        "system_id": profile.system_id,
        "service_id": profile.service_id,
        "workload_reference": profile.workload_reference,
        "horizon_rule": profile.horizon_rule,
        "outcome_threshold_rule": profile.threshold_version,
        "capture_schema_version": profile.capture_schema_version,
        "allowed_evidence_scope": profile.allowed_evidence_scope,
    }
    actual = {
        "system_id": lane.system_id,
        "service_id": lane.service_id,
        "workload_reference": lane.workload_reference,
        "horizon_rule": lane.horizon_rule,
        "outcome_threshold_rule": lane.outcome_threshold_rule,
        "capture_schema_version": lane.capture_schema_version,
        "allowed_evidence_scope": lane.allowed_evidence_scope,
    }
    if actual != expected:
        raise ValueError("capture does not match frozen pilot lane")


def _validate_prediction_fields(
    profile: ReplayPilotProfile,
    capture: ReplayCaptureRecord,
    prediction_fields: Mapping[str, Mapping[str, str]] | None,
) -> tuple[str, ...]:
    declared = (prediction_fields or {}).get(capture.lane.commit)
    if profile.allowed_prediction_fields or profile.forbidden_prediction_fields:
        if declared is None:
            raise ValueError("prediction-time field evidence is missing")
    if declared is None:
        return ()
    if not isinstance(declared, Mapping):
        raise ValueError("prediction-time field evidence is invalid")
    names = set(declared)
    if names - set(profile.allowed_prediction_fields):
        raise ValueError("prediction field is not allowed by frozen profile")
    if names & set(profile.forbidden_prediction_fields):
        raise ValueError("prediction field is forbidden by frozen profile")
    score_time = _parse_timestamp(capture.lane.score_time)
    for observed_at in declared.values():
        if _parse_timestamp(observed_at) > score_time:
            raise ValueError("prediction field is post-score-time")
    return tuple(sorted(names))


def normalize_replay_records(
    profile: ReplayPilotProfile,
    captures: Iterable[ReplayCaptureRecord],
    *,
    run_identity: str,
    prediction_fields: Mapping[str, Mapping[str, str]] | None = None,
) -> tuple[ReplayTerminalRecord, ...]:
    """Normalize every selected revision into one terminal evidence record."""

    if not run_identity.strip():
        raise ValueError("run_identity is required")
    records: list[ReplayTerminalRecord] = []
    seen: set[str] = set()
    for capture in captures:
        if not isinstance(capture, ReplayCaptureRecord):
            raise ValueError("capture record is invalid")
        commit = capture.lane.commit
        if commit not in profile.selected_commits:
            raise ValueError("capture commit is outside the selected sample")
        if commit in seen:
            raise ValueError("selected commit has multiple terminal records")
        _validate_lane(profile, capture)
        if (
            not capture.qualification_report_hash.strip()
            or not capture.execution_identity.strip()
        ):
            raise ValueError("capture lacks qualification or execution lineage")
        if (
            capture.deployment is not None
            and not capture.deployment.evidence_reference.strip()
        ):
            raise ValueError("deployment lacks evidence lineage")
        if any(
            artifact.state == "collected"
            and (
                not artifact.sha256
                or artifact.byte_count is None
                or artifact.byte_count < 0
            )
            for artifact in capture.artifacts
        ):
            raise ValueError("collected artifact lacks hash lineage")
        status, stage = _terminal_status(capture)
        reason = (
            capture.censor_reason
            if status in {"censored", "blocked-before-compilation"}
            else None
        )
        prediction_field_names = _validate_prediction_fields(
            profile, capture, prediction_fields
        )
        label = status if status in {"observed_positive", "observed_negative"} else None
        shared_observation_identity = (
            _hash(
                {
                    "event": profile.change_definition.event,
                    "observation_process": profile.change_definition.observation_process.canonical(),
                    "window": profile.change_definition.window.canonical(),
                    "thresholds": tuple(
                        threshold.canonical()
                        for threshold in profile.change_definition.thresholds
                    ),
                }
            )
            if label
            else ""
        )
        records.append(
            ReplayTerminalRecord(
                commit,
                capture.lane_identity,
                run_identity,
                status,
                stage,
                reason,
                capture,
                _artifact_manifest(capture),
                label,
                label,
                shared_observation_identity,
                prediction_field_names,
            )
        )
        seen.add(commit)
    missing = sorted(set(profile.selected_commits) - seen)
    if missing:
        raise ValueError(f"selected revisions lack terminal records: {missing}")
    return tuple(
        sorted(records, key=lambda item: profile.selected_commits.index(item.commit))
    )


def compare_repeatability(
    runs: Iterable[tuple[ReplayTerminalRecord, ...]],
) -> tuple[RepeatabilityCheck, ...]:
    """Compare repeated runs without averaging away disagreements."""

    run_list = tuple(runs)
    if len(run_list) < 2:
        return ()
    by_run = [dict((record.commit, record) for record in run) for run in run_list]
    commits = sorted(set().union(*(mapping for mapping in by_run)))
    checks: list[RepeatabilityCheck] = []
    for commit in commits:
        records = [mapping.get(commit) for mapping in by_run]
        discrepancies: list[str] = []
        if any(record is None for record in records):
            discrepancies.append("missing terminal record")
        present = [record for record in records if record is not None]
        statuses = {record.terminal_status for record in present}
        labels = {record.capture.outcome_class for record in present}
        family_labels = {
            (record.change_label, record.operational_label) for record in present
        }
        artifacts = {_canonical(record.artifact_manifest) for record in present}
        if len(statuses) > 1:
            discrepancies.append("terminal status differs")
        if len(labels) > 1:
            discrepancies.append("outcome label differs")
        if len(family_labels) > 1:
            discrepancies.append("family labels differ")
        if len(artifacts) > 1:
            discrepancies.append("artifact manifest differs")
        checks.append(
            RepeatabilityCheck(
                present[0].lane_identity if present else commit,
                tuple(sorted({record.run_identity for record in present})),
                len(statuses) <= 1 and len(present) == len(records),
                len(labels) <= 1 and len(present) == len(records),
                len(artifacts) <= 1 and len(present) == len(records),
                tuple(discrepancies),
                "pass" if not discrepancies else "fail",
            )
        )
    return tuple(checks)


def _counts(records: tuple[ReplayTerminalRecord, ...], selected: int) -> dict[str, int]:
    values = {status: 0 for status in TERMINAL_STATUSES}
    for record in records:
        values[record.terminal_status] += 1
    complete = values["observed_positive"] + values["observed_negative"]
    return {
        "selected": selected,
        "terminal": len(records),
        "complete_observations": complete,
        "observed_positive": values["observed_positive"],
        "observed_negative": values["observed_negative"],
        "censored": values["censored"],
        "blocked_before_compilation": values["blocked-before-compilation"],
        "release_withheld": sum(
            bool(
                record.capture.observation
                and (
                    record.capture.observation.uses_private_production_data
                    or record.capture.observation.uses_privileged_telemetry
                )
            )
            for record in records
        ),
    }


def _rate(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def build_stage2_feasibility_report(
    profile: ReplayPilotProfile,
    records: Iterable[ReplayTerminalRecord],
    *,
    repeatability: Iterable[RepeatabilityCheck] = (),
    throughput: Mapping[str, float] | None = None,
    temporal_coverage: Mapping[str, Any] | None = None,
    extrapolation: Mapping[str, Any] | None = None,
) -> FeasibilityReport:
    """Build a deterministic, claim-bounded feasibility report."""

    record_tuple = tuple(records)
    if len({record.commit for record in record_tuple}) != len(record_tuple):
        raise ValueError("report records must have unique commits")
    if {record.commit for record in record_tuple} != set(profile.selected_commits):
        raise ValueError("report records must cover the selected sample")
    counts = _counts(record_tuple, len(profile.selected_commits))
    complete = counts["complete_observations"]
    rates = {
        "terminal_coverage": _rate(counts["terminal"], counts["selected"]),
        "observation_rate": _rate(complete, counts["selected"]),
        "positive_rate": _rate(counts["observed_positive"], complete),
        "negative_rate": _rate(counts["observed_negative"], complete),
        "censor_rate": _rate(counts["censored"], counts["selected"]),
    }
    checks = tuple(repeatability)
    gates = [
        FeasibilityGate(
            "predeclaration_order", "pass", "predeclaration ancestry is verified", True
        ),
        FeasibilityGate(
            "commensurability",
            "pass",
            profile.commensurability().reason,
            profile.commensurability().level,
        ),
        FeasibilityGate(
            "terminal_coverage",
            "pass" if counts["terminal"] == counts["selected"] else "fail",
            "every selected revision has one terminal record",
            counts["terminal"],
        ),
        FeasibilityGate(
            "complete_observations",
            "pass" if complete >= profile.min_complete_records else "inconclusive",
            "complete observation count meets the declared pilot minimum"
            if complete >= profile.min_complete_records
            else "complete observation count is below the declared pilot minimum",
            complete,
        ),
        FeasibilityGate(
            "outcome_diversity",
            "pass"
            if not profile.require_both_outcomes
            or (counts["observed_positive"] > 0 and counts["observed_negative"] > 0)
            else "inconclusive",
            "both observed outcome classes are present"
            if not profile.require_both_outcomes
            or (counts["observed_positive"] > 0 and counts["observed_negative"] > 0)
            else "pilot lacks one observed outcome class",
            complete,
        ),
        FeasibilityGate(
            "observation_rate",
            "pass"
            if rates["observation_rate"] is not None
            and rates["observation_rate"] >= profile.min_observation_rate
            else "inconclusive",
            "complete observation rate meets the declared pilot minimum"
            if rates["observation_rate"] is not None
            and rates["observation_rate"] >= profile.min_observation_rate
            else "complete observation rate is below the declared pilot minimum",
            rates["observation_rate"],
        ),
        FeasibilityGate(
            "release_scope",
            "fail" if counts["release_withheld"] else "pass",
            "all observation evidence is public and unprivileged"
            if not counts["release_withheld"]
            else "private or privileged observation evidence is not releasable",
            counts["release_withheld"],
        ),
        FeasibilityGate(
            "repeatability",
            "pass"
            if not profile.require_repeatability
            else "pass"
            if checks and all(check.status == "pass" for check in checks)
            else "inconclusive",
            "repeatability is not required"
            if not profile.require_repeatability
            else "repeated lane executions agree"
            if checks and all(check.status == "pass" for check in checks)
            else "repeatability evidence is absent or disagrees",
            len(checks),
        ),
    ]
    hard_failures = {gate.gate_id for gate in gates if gate.status == "fail"}
    status = "blocked" if hard_failures else "feasible"
    if not hard_failures and any(gate.status != "pass" for gate in gates):
        status = "inconclusive"
    public_temporal = {
        **dict(temporal_coverage or {}),
        "score_times": tuple(
            sorted(record.capture.lane.score_time for record in record_tuple)
        ),
        "window_ends": tuple(
            sorted(record.capture.lane.window_end for record in record_tuple)
        ),
        "complete_windows": complete,
    }
    public_throughput = {
        str(key): float(value) for key, value in (throughput or {}).items()
    }
    public_extrapolation = dict(extrapolation or {})
    summaries = tuple(record.summary() for record in record_tuple)
    public = {
        "profile_identity": profile.profile_identity,
        "status": status,
        "counts": counts,
        "rates": rates,
        "temporal_coverage": public_temporal,
        "throughput": public_throughput,
        "repeatability": [check.to_dict() for check in checks],
        "release_readiness": {
            "published_artifacts": profile.published_artifacts,
            "allowed_evidence_scope": profile.allowed_evidence_scope,
            "withheld_count": counts["release_withheld"],
        },
        "gates": [gate.to_dict() for gate in gates],
        "extrapolation": public_extrapolation,
        "terminal_summaries": summaries,
        "claim_boundary": CLAIM_BOUNDARY,
        "claim_scope": "stage2_replay_feasibility_only",
    }
    return FeasibilityReport(
        _hash(public),
        profile.profile_identity,
        status,
        counts,
        rates,
        public_temporal,
        public_throughput,
        checks,
        public["release_readiness"],
        tuple(gates),
        public_extrapolation,
        summaries,
    )


def validate_stage2_feasibility_report(report: FeasibilityReport) -> None:
    """Validate public report identity and internal count invariants."""

    if not isinstance(report, FeasibilityReport):
        raise ValueError("report is invalid")
    counts = report.counts
    if counts["terminal"] != len(report.terminal_summaries):
        raise ValueError("report terminal count does not match summaries")
    if counts["selected"] < counts["terminal"]:
        raise ValueError("report terminal count exceeds selected count")
    if (
        counts["complete_observations"]
        != counts["observed_positive"] + counts["observed_negative"]
    ):
        raise ValueError("report complete count is inconsistent")
    if counts["terminal"] != sum(
        counts[key]
        for key in (
            "observed_positive",
            "observed_negative",
            "censored",
            "blocked_before_compilation",
        )
    ):
        raise ValueError("report terminal classes are inconsistent")
    public = report.to_dict()
    expected = _hash(
        {key: value for key, value in public.items() if key != "report_identity"}
    )
    if expected != report.report_identity:
        raise ValueError("report identity does not match canonical contents")


__all__ = [
    "CLAIM_BOUNDARY",
    "FeasibilityGate",
    "FeasibilityReport",
    "PILOT_STATUSES",
    "ReplayPilotProfile",
    "ReplayTerminalRecord",
    "RepeatabilityCheck",
    "build_stage2_feasibility_report",
    "compare_repeatability",
    "normalize_replay_records",
    "validate_stage2_feasibility_report",
]
