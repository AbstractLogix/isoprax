"""Stage 1 admission gate for paired-corpus evidence.

This module intentionally provides deterministic, offline checks that validate
whether a candidate corpus is admissible for Stage 1 evaluation workflows.
Passing admission is evidence infrastructure only and MUST NOT be treated as a
Semantic or Full conformance claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

_ALLOWED_SPLITS = ("train", "calibration_fit", "calibration_gate", "test")
_FORBIDDEN_LINKAGE_ONLY = {
    "timestamp_proximity",
    "text_similarity",
    "shared_authorship",
}


@dataclass(frozen=True)
class SplitDefinition:
    name: str
    start: str
    end: str

    def __post_init__(self) -> None:
        if self.name not in _ALLOWED_SPLITS:
            raise ValueError(f"invalid split name '{self.name}'")
        if _parse_iso(self.start) >= _parse_iso(self.end):
            raise ValueError(f"split '{self.name}' start must be before end")


@dataclass(frozen=True)
class AdmissionProfile:
    allowed_prediction_fields: frozenset[str]
    forbidden_prediction_fields: frozenset[str]
    horizon_rule: str
    horizon_frozen: bool
    adequacy_min_positives: int
    adequacy_min_negatives: int
    split_definitions: tuple[
        SplitDefinition, SplitDefinition, SplitDefinition, SplitDefinition
    ]
    release_scope: str
    thresholds_frozen: bool
    expected_system_id: str | None = None

    def __post_init__(self) -> None:
        if not self.horizon_rule.strip():
            raise ValueError("AdmissionProfile.horizon_rule must be non-empty")
        if self.adequacy_min_positives < 0 or self.adequacy_min_negatives < 0:
            raise ValueError("adequacy minimums must be >= 0")
        if not self.release_scope.strip():
            raise ValueError("release_scope metadata is required")

        names = [s.name for s in self.split_definitions]
        if tuple(names) != _ALLOWED_SPLITS:
            raise ValueError("split_definitions must be in canonical order")

        for i in range(1, len(self.split_definitions)):
            prev = self.split_definitions[i - 1]
            cur = self.split_definitions[i]
            if _parse_iso(prev.end) > _parse_iso(cur.start):
                raise ValueError("split_definitions must not overlap")


@dataclass(frozen=True)
class CorpusRow:
    row_id: str
    system_id: str
    change_id: str
    deployment_id: str
    observation_id: str
    split: str
    score_time: str
    outcome_class: str
    prediction_fields: dict[str, Any]
    linkage_bases: tuple[str, ...]
    outcome_window_complete: bool
    horizon_rule_used: str
    threshold_version: str
    change_group_id: str | None = None
    censor_reason: str | None = None

    def __post_init__(self) -> None:
        if self.split not in _ALLOWED_SPLITS:
            raise ValueError(f"invalid row split '{self.split}'")
        if self.outcome_class not in {
            "observed_positive",
            "observed_negative",
            "censored",
        }:
            raise ValueError(f"invalid outcome_class '{self.outcome_class}'")
        _parse_iso(self.score_time)


@dataclass(frozen=True)
class GateResult:
    gate_id: str
    passed: bool
    message: str
    failed_row_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdmissionReport:
    admissible: bool
    gate_results: tuple[GateResult, ...]
    counts_by_split: dict[str, dict[str, int]]
    manifest: dict[str, Any]
    declarable_class: str = "Admission evidence only; conformance class not assigned"


def evaluate_admission(
    rows: list[CorpusRow], profile: AdmissionProfile
) -> AdmissionReport:
    """Evaluate Stage 1 admission gates deterministically."""
    ordered_rows = sorted(rows, key=lambda r: r.row_id)
    gates: list[GateResult] = [
        _gate_lineage_and_linkage(ordered_rows),
        _gate_prediction_time_fields(ordered_rows, profile),
        _gate_outcome_classes_and_censoring(ordered_rows),
        _gate_split_and_followup(ordered_rows, profile),
        _gate_horizon_and_threshold_freeze(ordered_rows, profile),
        _gate_single_system_boundary(ordered_rows, profile),
        _gate_cluster_by_change(ordered_rows),
        _gate_adequacy(ordered_rows, profile),
        _gate_manifest_metadata(profile),
    ]

    counts = _counts_by_split(ordered_rows)
    manifest = {
        "splits": [
            {"name": s.name, "start": s.start, "end": s.end}
            for s in profile.split_definitions
        ],
        "counts_by_split": counts,
        "horizon_rule": profile.horizon_rule,
        "horizon_frozen": profile.horizon_frozen,
        "release_scope": profile.release_scope,
        "thresholds_frozen": profile.thresholds_frozen,
        "expected_system_id": profile.expected_system_id,
    }
    admissible = all(g.passed for g in gates)
    return AdmissionReport(
        admissible=admissible,
        gate_results=tuple(gates),
        counts_by_split=counts,
        manifest=manifest,
    )


def _gate_lineage_and_linkage(rows: list[CorpusRow]) -> GateResult:
    failed: list[str] = []
    for r in rows:
        required = [
            r.row_id,
            r.system_id,
            r.change_id,
            r.deployment_id,
            r.observation_id,
        ]
        if not all(v.strip() for v in required):
            failed.append(r.row_id)
            continue
        linkage = tuple(x.strip() for x in r.linkage_bases if x.strip())
        if not linkage:
            failed.append(r.row_id)
            continue
        if len(linkage) == 1 and linkage[0] in _FORBIDDEN_LINKAGE_ONLY:
            failed.append(r.row_id)
    if failed:
        return GateResult(
            gate_id="lineage_linkage",
            passed=False,
            message="lineage ids missing or linkage based only on forbidden heuristics",
            failed_row_ids=tuple(sorted(failed)),
        )
    return GateResult("lineage_linkage", True, "lineage and linkage gate passed")


def _gate_prediction_time_fields(
    rows: list[CorpusRow], profile: AdmissionProfile
) -> GateResult:
    failed: list[str] = []
    for r in rows:
        keys = set(r.prediction_fields.keys())
        if keys - set(profile.allowed_prediction_fields):
            failed.append(r.row_id)
            continue
        if keys & set(profile.forbidden_prediction_fields):
            failed.append(r.row_id)
            continue
    if failed:
        return GateResult(
            gate_id="prediction_time_fields",
            passed=False,
            message="prediction-time fields violate allowlist/forbidden rules",
            failed_row_ids=tuple(sorted(failed)),
        )
    return GateResult(
        "prediction_time_fields", True, "prediction-time field gate passed"
    )


def _gate_outcome_classes_and_censoring(rows: list[CorpusRow]) -> GateResult:
    failed: list[str] = []
    for r in rows:
        if r.outcome_class == "observed_negative" and not r.outcome_window_complete:
            failed.append(r.row_id)
        if r.outcome_class == "censored" and (
            r.censor_reason is None or not r.censor_reason.strip()
        ):
            failed.append(r.row_id)
    if failed:
        return GateResult(
            gate_id="outcome_censoring",
            passed=False,
            message="outcome class/censoring constraints violated",
            failed_row_ids=tuple(sorted(failed)),
        )
    return GateResult("outcome_censoring", True, "outcome and censoring gate passed")


def _gate_split_and_followup(
    rows: list[CorpusRow], profile: AdmissionProfile
) -> GateResult:
    split_by_name = {s.name: s for s in profile.split_definitions}
    failed: list[str] = []
    for r in rows:
        split = split_by_name[r.split]
        t = _parse_iso(r.score_time)
        if t < _parse_iso(split.start) or t > _parse_iso(split.end):
            failed.append(r.row_id)
            continue
        if r.outcome_class != "censored" and not r.outcome_window_complete:
            failed.append(r.row_id)
    if failed:
        return GateResult(
            gate_id="split_followup",
            passed=False,
            message="split membership or follow-up completeness violated",
            failed_row_ids=tuple(sorted(failed)),
        )
    return GateResult("split_followup", True, "split/follow-up gate passed")


def _gate_horizon_and_threshold_freeze(
    rows: list[CorpusRow], profile: AdmissionProfile
) -> GateResult:
    failed: list[str] = []
    if not profile.horizon_frozen or not profile.thresholds_frozen:
        return GateResult(
            gate_id="horizon_threshold_freeze",
            passed=False,
            message="horizon/threshold metadata must be frozen before admission",
        )
    for r in rows:
        if r.horizon_rule_used != profile.horizon_rule:
            failed.append(r.row_id)
        if not r.threshold_version.strip():
            failed.append(r.row_id)
    if failed:
        return GateResult(
            gate_id="horizon_threshold_freeze",
            passed=False,
            message="row horizon/threshold metadata mismatch",
            failed_row_ids=tuple(sorted(set(failed))),
        )
    return GateResult(
        "horizon_threshold_freeze", True, "horizon/threshold freeze gate passed"
    )


def _gate_single_system_boundary(
    rows: list[CorpusRow], profile: AdmissionProfile
) -> GateResult:
    systems = {r.system_id for r in rows}
    if profile.expected_system_id and systems != {profile.expected_system_id}:
        return GateResult(
            gate_id="single_system_boundary",
            passed=False,
            message="rows must match expected_system_id",
            failed_row_ids=tuple(
                sorted(
                    r.row_id for r in rows if r.system_id != profile.expected_system_id
                )
            ),
        )
    if len(systems) > 1:
        return GateResult(
            gate_id="single_system_boundary",
            passed=False,
            message="cross-system pooling is forbidden in a single admitted corpus",
            failed_row_ids=tuple(sorted(r.row_id for r in rows)),
        )
    return GateResult(
        "single_system_boundary", True, "single-system boundary gate passed"
    )


def _gate_cluster_by_change(rows: list[CorpusRow]) -> GateResult:
    split_by_change: dict[str, set[str]] = {}
    for r in rows:
        key = r.change_group_id or r.change_id
        split_by_change.setdefault(key, set()).add(r.split)
    leaking = sorted(k for k, v in split_by_change.items() if len(v) > 1)
    if leaking:
        failed = tuple(
            sorted(
                r.row_id for r in rows if (r.change_group_id or r.change_id) in leaking
            )
        )
        return GateResult(
            gate_id="cluster_by_change",
            passed=False,
            message="rows derived from one change must not span multiple splits",
            failed_row_ids=failed,
        )
    return GateResult("cluster_by_change", True, "cluster-by-change gate passed")


def _gate_adequacy(rows: list[CorpusRow], profile: AdmissionProfile) -> GateResult:
    counts = _counts_by_split(rows)
    deficits: list[str] = []
    for split in _ALLOWED_SPLITS:
        positives = counts[split]["observed_positive"]
        negatives = counts[split]["observed_negative"]
        if (
            positives < profile.adequacy_min_positives
            or negatives < profile.adequacy_min_negatives
        ):
            deficits.append(split)
    if deficits:
        return GateResult(
            gate_id="adequacy",
            passed=False,
            message=(
                "per-split adequacy floor not met for observed_positive/observed_negative"
            ),
            failed_row_ids=tuple(deficits),
        )
    return GateResult("adequacy", True, "adequacy gate passed")


def _gate_manifest_metadata(profile: AdmissionProfile) -> GateResult:
    if not profile.release_scope.strip():
        return GateResult(
            gate_id="manifest_metadata",
            passed=False,
            message="release_scope metadata is required",
        )
    return GateResult("manifest_metadata", True, "manifest metadata gate passed")


def _counts_by_split(rows: list[CorpusRow]) -> dict[str, dict[str, int]]:
    out = {
        split: {
            "observed_positive": 0,
            "observed_negative": 0,
            "censored": 0,
        }
        for split in _ALLOWED_SPLITS
    }
    for r in rows:
        out[r.split][r.outcome_class] += 1
    return out


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts)
