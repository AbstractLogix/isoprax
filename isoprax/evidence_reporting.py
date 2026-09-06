"""Deterministic, claim-bounded Stage 1 evidence reporting."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from .admission import AdmissionProfile, AdmissionReport
from .corpus_assembly import CorpusAssemblyReport
from .replay_capture import ReplayCaptureRecord

_CLAIM_BOUNDARY = (
    "Admission evidence only; build qualification, replay observation, corpus "
    "assembly, and Stage 1 admission do not establish Semantic or Full "
    "Conformance, model efficacy, or cross-family score pooling."
)
_STATUSES = {"admission_evidence", "blocked", "inconclusive"}


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _hash(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class EvidenceReportProfile:
    assembly_profile_identity: str
    release_scope: str
    predeclaration_artifact_hash: str
    predeclaration_anchor_reference: str
    published_artifacts: tuple[str, ...]
    required_evidence_categories: tuple[str, ...]

    def __post_init__(self) -> None:
        required = (
            self.assembly_profile_identity,
            self.release_scope,
            self.predeclaration_artifact_hash,
            self.predeclaration_anchor_reference,
        )
        if not all(isinstance(value, str) and value.strip() for value in required):
            raise ValueError("evidence report profile metadata is required")
        for values, name in (
            (self.published_artifacts, "published artifacts"),
            (self.required_evidence_categories, "required evidence categories"),
        ):
            if not values or len(set(values)) != len(values) or any(
                not isinstance(value, str) or not value.strip() for value in values
            ):
                raise ValueError(f"{name} must be non-empty and unique")


@dataclass(frozen=True)
class UnavailableEvidence:
    category: str
    reason: str


@dataclass(frozen=True)
class GateSummary:
    gate_id: str
    passed: bool
    message: str
    failed_count: int


@dataclass(frozen=True)
class EvidenceReport:
    report_identity: str
    status: str
    assembly_profile_identity: str
    release_scope: str
    predeclaration: dict[str, str]
    published_artifacts: tuple[str, ...]
    capture_evidence: tuple[dict[str, Any], ...]
    counts: dict[str, int]
    provenance: dict[str, Any]
    gates: tuple[GateSummary, ...]
    unavailable_evidence: tuple[UnavailableEvidence, ...]
    claim_boundary: str = _CLAIM_BOUNDARY
    claim_scope: str = "stage1_evidence_reporting_only"

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_identity": self.report_identity,
            "status": self.status,
            "assembly_profile_identity": self.assembly_profile_identity,
            "release_scope": self.release_scope,
            "predeclaration": self.predeclaration,
            "published_artifacts": list(self.published_artifacts),
            "capture_evidence": list(self.capture_evidence),
            "counts": self.counts,
            "provenance": self.provenance,
            "gates": [gate.__dict__ for gate in self.gates],
            "unavailable_evidence": [item.__dict__ for item in self.unavailable_evidence],
            "claim_boundary": self.claim_boundary,
            "claim_scope": self.claim_scope,
        }


def _validate_profile(
    profile: EvidenceReportProfile,
    assembly: CorpusAssemblyReport,
    admission_profile: AdmissionProfile,
    admission: AdmissionReport,
) -> None:
    if assembly.claim_scope != "corpus_assembly_evidence_only":
        raise ValueError("assembly claim scope is invalid")
    manifest = assembly.manifest_input
    if profile.assembly_profile_identity != assembly.profile_identity:
        raise ValueError("assembly profile identity does not match")
    if any(
        scope != profile.release_scope
        for scope in (manifest.get("release_scope"), admission_profile.release_scope)
    ):
        raise ValueError("release scope does not match")
    if tuple(manifest.get("published_artifacts", ())) != profile.published_artifacts:
        raise ValueError("published artifacts do not match assembly")
    if admission_profile.published_artifacts != profile.published_artifacts:
        raise ValueError("published artifacts do not match admission")
    if admission.manifest.get("release_scope") != profile.release_scope:
        raise ValueError("admission report release scope does not match")
    if tuple(admission.manifest.get("published_artifacts", ())) != profile.published_artifacts:
        raise ValueError("admission report artifacts do not match")
    predeclaration = admission_profile.predeclaration_evidence
    if (
        predeclaration is None
        or predeclaration.artifact_hash != profile.predeclaration_artifact_hash
        or predeclaration.external_anchor_reference
        != profile.predeclaration_anchor_reference
    ):
        raise ValueError("predeclaration evidence does not match")
    provenance = admission_profile.corpus_provenance
    if (
        provenance is None
        or provenance.uses_private_production_data
        or provenance.uses_privileged_telemetry
    ):
        raise ValueError("provenance is not publishable")


def _capture_summary(capture: ReplayCaptureRecord) -> tuple[dict[str, Any], set[str]]:
    if capture.claim_scope != "replay_observation_evidence_only":
        raise ValueError("capture claim scope is invalid")
    if capture.deployment is None or capture.observation is None:
        raise ValueError("capture lineage is incomplete")
    if (
        capture.observation.uses_private_production_data
        or capture.observation.uses_privileged_telemetry
    ):
        raise ValueError("capture evidence is not publishable")
    artifact_states = tuple(
        {
            "path": artifact.path,
            "state": artifact.state,
            "sha256": artifact.sha256,
            "byte_count": artifact.byte_count,
        }
        for artifact in sorted(capture.artifacts, key=lambda artifact: artifact.path)
    )
    available: set[str] = set()
    if capture.qualification_report_hash.strip():
        available.add("build_qualification")
    if capture.execution_identity.strip():
        available.add("runner_execution")
    if artifact_states and all(item["state"] == "collected" for item in artifact_states):
        available.add("capture_artifacts")
    return (
        {
            "lane_identity": capture.lane_identity,
            "qualification_report_hash": capture.qualification_report_hash,
            "execution_identity": capture.execution_identity,
            "deployment_reference": capture.deployment.evidence_reference,
            "outcome_class": capture.outcome_class,
            "censor_reason": capture.censor_reason,
            "artifact_states": artifact_states,
        },
        available,
    )


def _validated_captures(
    assembly: CorpusAssemblyReport, captures: Iterable[ReplayCaptureRecord]
) -> tuple[tuple[dict[str, Any], ...], set[str]]:
    by_lane: dict[str, ReplayCaptureRecord] = {}
    for capture in captures:
        if not isinstance(capture, ReplayCaptureRecord) or capture.lane_identity in by_lane:
            raise ValueError("capture records must be unique and valid")
        by_lane[capture.lane_identity] = capture
    summaries: list[dict[str, Any]] = []
    available: set[str] | None = None
    if len(by_lane) != len(assembly.rows):
        raise ValueError("accepted rows must have exactly one capture")
    for row in assembly.rows:
        capture = by_lane.get(row.observation_id)
        if (
            capture is None
            or capture.lane.system_id != row.system_id
            or capture.lane.commit != row.change_id
            or capture.deployment is None
            or capture.deployment.evidence_reference != row.deployment_id
            or capture.outcome_class != row.outcome_class
        ):
            raise ValueError("capture does not match accepted row")
        summary, present = _capture_summary(capture)
        summaries.append(summary)
        available = present if available is None else available & present
    return (
        tuple(sorted(summaries, key=lambda item: item["lane_identity"])),
        (available or set()),
    )


def build_evidence_report(
    profile: EvidenceReportProfile,
    assembly: CorpusAssemblyReport,
    captures: Iterable[ReplayCaptureRecord],
    admission_profile: AdmissionProfile,
    admission: AdmissionReport,
) -> EvidenceReport:
    """Reduce validated Stage 1 evidence to a deterministic public report."""
    _validate_profile(profile, assembly, admission_profile, admission)
    capture_evidence, available = _validated_captures(assembly, captures)
    gates = tuple(
        GateSummary(gate.gate_id, gate.passed, gate.message, len(gate.failed_row_ids))
        for gate in sorted(admission.gate_results, key=lambda gate: gate.gate_id)
    )
    unavailable = tuple(
        UnavailableEvidence(category, "not collected or incomplete")
        for category in profile.required_evidence_categories
        if category not in available
    )
    if not admission.admissible:
        status = "blocked"
    elif unavailable:
        status = "inconclusive"
    else:
        status = "admission_evidence"
    counts = {"accepted_rows": len(assembly.rows), "rejected_inputs": len(assembly.rejections)}
    counts.update({key: int(value) for key, value in sorted(assembly.counts.items())})
    provenance = admission_profile.corpus_provenance
    public = {
        "status": status,
        "assembly_profile_identity": assembly.profile_identity,
        "release_scope": profile.release_scope,
        "predeclaration": {"artifact_hash": profile.predeclaration_artifact_hash, "anchor_reference": profile.predeclaration_anchor_reference},
        "published_artifacts": list(profile.published_artifacts),
        "capture_evidence": capture_evidence,
        "counts": counts,
        "provenance": {"source_system": provenance.source_system, "uses_private_production_data": False, "uses_privileged_telemetry": False},
        "gates": [gate.__dict__ for gate in gates],
        "unavailable_evidence": [item.__dict__ for item in unavailable],
        "claim_boundary": _CLAIM_BOUNDARY,
        "claim_scope": "stage1_evidence_reporting_only",
    }
    return EvidenceReport(
        report_identity=_hash(public),
        status=status,
        assembly_profile_identity=assembly.profile_identity,
        release_scope=profile.release_scope,
        predeclaration=public["predeclaration"],
        published_artifacts=profile.published_artifacts,
        capture_evidence=capture_evidence,
        counts=counts,
        provenance=public["provenance"],
        gates=gates,
        unavailable_evidence=unavailable,
    )


__all__ = [
    "EvidenceReport",
    "EvidenceReportProfile",
    "GateSummary",
    "UnavailableEvidence",
    "build_evidence_report",
]
