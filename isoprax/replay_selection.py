"""Deterministic replay candidate screening and predeclaration provenance.

This module stays intentionally narrow: it models the candidate screening and
plan-predeclaration checks required to keep replay work evidence-boundary-safe
without importing real-data evaluation or profile logic.
"""

from __future__ import annotations

import hashlib
import json
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, Mapping, Sequence

_CANONICAL_SCREEN_ORDER = (
    "commit_supply",
    "licence_terms",
    "build_rate",
    "prediction_metadata",
)
_NO_CHANGE_EVENT_SENTINEL = "no Change-family event exists to condition on"
_COMMENSURABILITY_SENTINEL = "Isoprax v0.3 §5.6"
_REPLAY_JUSTIFICATION_SENTINEL = "Deterministic replay remains structurally justified"
_KNOWN_EXCLUSION_TYPES = {
    "structural_no_change_events",
    "commensurability_mismatch",
    "structural_replay_justification",
}


def _coerce_mapping(candidate: Any) -> Mapping[str, Any]:
    if isinstance(candidate, Mapping):
        return candidate
    if hasattr(candidate, "__dict__"):
        return {k: v for k, v in vars(candidate).items() if not k.startswith("_")}
    raise TypeError("candidate must be a mapping or dataclass-like object")


def _pick(candidate: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in candidate and candidate[name] is not None:
            return candidate[name]
    return default


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "allowed"}
    return bool(value)


@dataclass(frozen=True)
class ScreeningResult:
    screen_name: str
    screen_number: int
    passed: bool
    detail: str


@dataclass(frozen=True)
class CandidateRecord:
    system_id: str
    eligible: bool
    disqualifying_screen: str | None
    screen_results: tuple[ScreeningResult, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.system_id.strip():
            raise ValueError("system_id is required")


@dataclass(frozen=True)
class PredeclarationArtifact:
    artifact_id: str
    content: str
    soak_duration: str
    soak_duration_rule: str
    positive_event_definition: str
    positive_event_thresholds: dict[str, Any]
    censoring_rule: str
    drift_threshold: float | int
    anchor_threshold: float | int
    split_boundaries: dict[str, tuple[str, str]]
    adequacy_floor: int
    ablation_comparison_plan: str

    def __post_init__(self) -> None:
        if not self.artifact_id.strip():
            raise ValueError("artifact_id is required")
        if not self.content.strip():
            raise ValueError("artifact content is required")
        if not self.soak_duration.strip():
            raise ValueError("soak_duration is required")
        if not self.soak_duration_rule.strip():
            raise ValueError("soak_duration_rule is required")
        if not self.positive_event_definition.strip():
            raise ValueError("positive_event_definition is required")
        if not isinstance(self.positive_event_thresholds, dict) or not self.positive_event_thresholds:
            raise ValueError("positive_event_thresholds is required")
        if not self.censoring_rule.strip():
            raise ValueError("censoring_rule is required")
        if not isinstance(self.split_boundaries, dict) or not self.split_boundaries:
            raise ValueError("split_boundaries is required")
        if self.adequacy_floor < 0:
            raise ValueError("adequacy_floor must be non-negative")
        if not self.ablation_comparison_plan.strip():
            raise ValueError("ablation_comparison_plan is required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "content": self.content,
            "soak_duration": self.soak_duration,
            "soak_duration_rule": self.soak_duration_rule,
            "positive_event_definition": self.positive_event_definition,
            "positive_event_thresholds": self.positive_event_thresholds,
            "censoring_rule": self.censoring_rule,
            "drift_threshold": self.drift_threshold,
            "anchor_threshold": self.anchor_threshold,
            "split_boundaries": {
                name: [start, end] for name, (start, end) in self.split_boundaries.items()
            },
            "adequacy_floor": self.adequacy_floor,
            "ablation_comparison_plan": self.ablation_comparison_plan,
        }


@dataclass(frozen=True)
class ProvenanceRecord:
    artifact_hash: str
    predeclaration_commit: str
    external_anchor_type: str | None
    external_anchor_reference: str | None
    ancestry_ok: bool
    predeclared_before_data: bool
    anchored: bool
    records: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExclusionEntry:
    dataset_id: str
    exclusion_type: str
    reason: str
    residual_use: str | None = None
    pending: bool = False
    cited_spec: str | None = None

    def __post_init__(self) -> None:
        if not self.dataset_id.strip():
            raise ValueError("dataset_id is required")
        if not self.reason.strip():
            raise ValueError("reason is required")
        if self.exclusion_type not in _KNOWN_EXCLUSION_TYPES:
            raise ValueError(f"unsupported exclusion_type '{self.exclusion_type}'")
        reason_lower = self.reason.lower()
        if self.pending or "pending" in reason_lower or "deferred" in reason_lower:
            raise ValueError("exclusion entries must not describe a pending or deferred path")
        if self.exclusion_type == "structural_no_change_events" and _NO_CHANGE_EVENT_SENTINEL.lower() not in reason_lower:
            raise ValueError("structural no-change exclusion must state the absence of a Change-family event")
        if self.exclusion_type == "commensurability_mismatch" and _COMMENSURABILITY_SENTINEL.lower() not in reason_lower:
            raise ValueError("commensurability exclusion must cite Isoprax v0.3 §5.6")
        if self.exclusion_type == "structural_replay_justification" and _REPLAY_JUSTIFICATION_SENTINEL.lower() not in reason_lower:
            raise ValueError("replay justification exclusion must state that deterministic replay is structurally justified")


def _screen_commit_supply(
    candidate: Mapping[str, Any], *, adequacy_floor: int = 0, positive_event_rate: float | None = None
) -> tuple[bool, str]:
    supply = _pick(candidate, "commit_supply", "commit_capacity", default=None)
    if supply is None:
        return False, "Screen 1 failed: commit supply is missing"
    try:
        supply_value = float(supply)
    except (TypeError, ValueError):
        return False, "Screen 1 failed: commit supply is invalid"
    rate = _pick(candidate, "observed_positive_rate", "positive_event_rate", default=positive_event_rate)
    if rate is None:
        rate = _pick(candidate, "estimated_positive_event_rate", default=0.0)
    try:
        rate_value = float(rate)
    except (TypeError, ValueError):
        rate_value = 0.0
    if rate_value <= 0.0:
        projected = 0.0
    else:
        projected = supply_value * rate_value
    if projected < float(adequacy_floor):
        return (
            False,
            "Screen 1 failed: projected commit supply below the adequacy floor for the observed positive-event rate",
        )
    return True, "Screen 1 passed: commit supply supports the adequacy floor"


def _screen_licence_terms(candidate: Mapping[str, Any]) -> tuple[bool, str]:
    publication_forbidden = _as_bool(
        _pick(
            candidate,
            "licence_forbids_publication",
            "license_forbids_publication",
            "publication_forbidden",
            "forbid_publication",
            default=False,
        ),
        default=False,
    )
    redistribution_forbidden = _as_bool(
        _pick(
            candidate,
            "licence_forbids_redistribution",
            "license_forbids_redistribution",
            "redistribution_forbidden",
            "forbid_redistribution",
            default=False,
        ),
        default=False,
    )
    if publication_forbidden or redistribution_forbidden:
        return (
            False,
            "Screen 2 failed: licence forbids publication of measurements or redistribution of derived metrics",
        )
    return True, "Screen 2 passed: licence terms permit publication and redistribution"


def _screen_build_rate(
    candidate: Mapping[str, Any], *, build_floor: float = 0.95, allow_clustered_failures: bool = False
) -> tuple[bool, str]:
    success_rate = _pick(candidate, "sampled_build_success_rate", "build_success_rate", default=None)
    if success_rate is None:
        return False, "Screen 3 failed: sampled build success rate is missing"
    try:
        rate_value = float(success_rate)
    except (TypeError, ValueError):
        return False, "Screen 3 failed: sampled build success rate is invalid"
    attempts = _pick(candidate, "build_attempts", "sampled_build_attempts", default=0)
    try:
        attempts_value = int(attempts)
    except (TypeError, ValueError):
        attempts_value = 0
    if attempts_value <= 0:
        return False, "Screen 3 failed: build-attempt sample is missing"
    if rate_value < float(build_floor):
        return False, "Screen 3 failed: sampled build success rate falls below the predeclared floor"
    clustered_failures = _as_bool(
        _pick(candidate, "build_failures_clustered", "clustered_failures", default=False),
        default=False,
    )
    if clustered_failures and not allow_clustered_failures:
        return False, "Screen 3 failed: build failures cluster in time and would bias the corpus"
    return True, "Screen 3 passed: build success rate and temporal stability are acceptable"


def _screen_prediction_metadata(candidate: Mapping[str, Any]) -> tuple[bool, str]:
    populated = _as_bool(
        _pick(
            candidate,
            "prediction_time_feature_allowlist_populatable",
            "metadata_allowlist_populatable",
            "prediction_metadata_available",
            default=True,
        ),
        default=True,
    )
    if not populated:
        return False, "Screen 4 failed: prediction-time feature allowlist cannot be populated at sampled commits"
    return True, "Screen 4 passed: prediction-time feature allowlist is populatable"


def _order_screen_results(
    candidate: Mapping[str, Any],
    *,
    adequacy_floor: int,
    build_floor: float,
    allow_clustered_failures: bool = False,
) -> list[ScreeningResult]:
    screens = (
        ("commit_supply", _screen_commit_supply(candidate, adequacy_floor=adequacy_floor)),
        ("licence_terms", _screen_licence_terms(candidate)),
        ("build_rate", _screen_build_rate(candidate, build_floor=build_floor, allow_clustered_failures=allow_clustered_failures)),
        ("prediction_metadata", _screen_prediction_metadata(candidate)),
    )
    results: list[ScreeningResult] = []
    for index, (name, (passed, detail)) in enumerate(screens, start=1):
        results.append(ScreeningResult(screen_name=name, screen_number=index, passed=passed, detail=detail))
        if not passed:
            break
    return results


def screen_candidate(
    candidate: Any,
    *,
    adequacy_floor: int = 0,
    build_floor: float = 0.95,
    allow_clustered_failures: bool = False,
) -> CandidateRecord:
    """Screen one candidate system in the required fixed order."""
    candidate_map = _coerce_mapping(candidate)
    system_id = str(_pick(candidate_map, "system_id", "candidate_id", default="candidate")).strip()
    results = _order_screen_results(
        candidate_map,
        adequacy_floor=adequacy_floor,
        build_floor=build_floor,
        allow_clustered_failures=allow_clustered_failures,
    )
    first_failure = next((result for result in results if not result.passed), None)
    if first_failure is not None:
        return CandidateRecord(
            system_id=system_id,
            eligible=False,
            disqualifying_screen=first_failure.screen_name,
            screen_results=tuple(results),
            metadata={
                "adequacy_floor": adequacy_floor,
                "build_floor": build_floor,
                "allow_clustered_failures": allow_clustered_failures,
            },
        )
    return CandidateRecord(
        system_id=system_id,
        eligible=True,
        disqualifying_screen=None,
        screen_results=tuple(results),
        metadata={
            "adequacy_floor": adequacy_floor,
            "build_floor": build_floor,
            "allow_clustered_failures": allow_clustered_failures,
        },
    )


def screen_candidates(
    candidates: Iterable[Any],
    *,
    adequacy_floor: int = 0,
    build_floor: float = 0.95,
    allow_clustered_failures: bool = False,
) -> tuple[CandidateRecord, ...]:
    """Return a record for every candidate considered, preserving screen order."""
    return tuple(
        screen_candidate(
            candidate,
            adequacy_floor=adequacy_floor,
            build_floor=build_floor,
            allow_clustered_failures=allow_clustered_failures,
        )
        for candidate in candidates
    )


def evaluate_candidate_screening(
    candidates: Iterable[Any],
    *,
    adequacy_floor: int = 0,
    build_floor: float = 0.95,
    allow_clustered_failures: bool = False,
) -> tuple[CandidateRecord, ...]:
    """Compatibility wrapper; prefer screen_candidates()."""
    warnings.warn(
        "evaluate_candidate_screening() is a compatibility alias for screen_candidates(); prefer the primary API.",
        DeprecationWarning,
        stacklevel=2,
    )
    return screen_candidates(
        candidates,
        adequacy_floor=adequacy_floor,
        build_floor=build_floor,
        allow_clustered_failures=allow_clustered_failures,
    )


def screen_candidate_system(
    candidate: Any,
    *,
    adequacy_floor: int = 0,
    build_floor: float = 0.95,
    allow_clustered_failures: bool = False,
) -> CandidateRecord:
    """Compatibility wrapper; prefer screen_candidate()."""
    warnings.warn(
        "screen_candidate_system() is a compatibility alias for screen_candidate(); prefer the primary API.",
        DeprecationWarning,
        stacklevel=2,
    )
    return screen_candidate(
        candidate,
        adequacy_floor=adequacy_floor,
        build_floor=build_floor,
        allow_clustered_failures=allow_clustered_failures,
    )


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def hash_predeclaration_artifact(artifact: PredeclarationArtifact | Mapping[str, Any]) -> str:
    payload = artifact.to_dict() if isinstance(artifact, PredeclarationArtifact) else dict(artifact)
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


compute_predeclaration_hash = hash_predeclaration_artifact


def validate_predeclaration_artifact(
    artifact: PredeclarationArtifact | Mapping[str, Any],
    *,
    expected_hash: str | None = None,
    observation_window: str | None = None,
) -> bool:
    """Accept only a structurally complete predeclaration that uses training-only soak derivation."""
    if isinstance(artifact, Mapping):
        split_boundaries_raw = dict(artifact.get("split_boundaries", {}))
        split_boundaries: dict[str, tuple[str, str]] = {}
        for name, value in split_boundaries_raw.items():
            if isinstance(value, Mapping):
                start = str(value.get("start", ""))
                end = str(value.get("end", ""))
                split_boundaries[name] = (start, end)
                continue
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                if len(value) != 2:
                    raise ValueError(f"split_boundaries[{name}] must contain exactly two values")
                split_boundaries[name] = (str(value[0]), str(value[1]))
                continue
            raise ValueError(f"split_boundaries[{name}] must be a sequence or mapping")
        artifact_obj = PredeclarationArtifact(
            artifact_id=str(artifact.get("artifact_id", "artifact")),
            content=str(artifact.get("content", "")),
            soak_duration=str(artifact.get("soak_duration", "")),
            soak_duration_rule=str(artifact.get("soak_duration_rule", "")),
            positive_event_definition=str(artifact.get("positive_event_definition", "")),
            positive_event_thresholds=dict(artifact.get("positive_event_thresholds", {})),
            censoring_rule=str(artifact.get("censoring_rule", "")),
            drift_threshold=artifact.get("drift_threshold", 0),
            anchor_threshold=artifact.get("anchor_threshold", 0),
            split_boundaries=split_boundaries,
            adequacy_floor=int(artifact.get("adequacy_floor", 0)),
            ablation_comparison_plan=str(artifact.get("ablation_comparison_plan", "")),
        )
    else:
        artifact_obj = artifact

    if not artifact_obj.content.strip():
        raise ValueError("predeclaration artifact content is required")
    if expected_hash is not None:
        actual_hash = hash_predeclaration_artifact(artifact_obj)
        if actual_hash != expected_hash:
            raise ValueError("predeclaration artifact hash mismatch")
    rule = (artifact_obj.soak_duration_rule or "").lower()
    if observation_window is not None and "observation" in rule and "training" not in rule:
        raise ValueError("soak duration must be derived from training-period-only data, not the observation window")
    if "observation window" in rule and "training" not in rule:
        raise ValueError("soak duration rule cannot use the observation window it bounds")
    return True


validate_predeclaration = validate_predeclaration_artifact


def _infer_commit_time(commit: str, *, timestamps: Mapping[str, Any] | None = None) -> datetime | None:
    if timestamps is not None and commit in timestamps:
        value = timestamps[commit]
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
    return None


def _ancestor_check(
    predeclaration_commit: str,
    corpus_data_commits: Iterable[str],
    *,
    ancestry_graph: Mapping[str, Sequence[str]] | None = None,
    timestamps: Mapping[str, Any] | None = None,
) -> bool:
    if not predeclaration_commit:
        return False
    corpora = tuple(corpus_data_commits)
    if not corpora:
        return True
    if ancestry_graph is not None:
        for commit in corpora:
            visited: set[str] = set()
            stack = [commit]
            found = False
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                if current == predeclaration_commit:
                    found = True
                    break
                stack.extend(ancestry_graph.get(current, ()))
            if not found:
                return False
        return True
    predecl_time = _infer_commit_time(predeclaration_commit, timestamps=timestamps)
    for commit in corpora:
        commit_time = _infer_commit_time(commit, timestamps=timestamps)
        if predecl_time is not None and commit_time is not None and commit_time < predecl_time:
            return False
    return True


def evaluate_predeclaration_provenance(
    artifact: PredeclarationArtifact | Mapping[str, Any],
    *,
    artifact_hash: str | None = None,
    predeclaration_commit: str | None = None,
    corpus_data_commits: Iterable[str] = (),
    external_anchor: Mapping[str, Any] | None = None,
    remote_configured: bool = False,
    repository_pushed: bool = False,
    ancestry_graph: Mapping[str, Sequence[str]] | None = None,
    commit_timestamps: Mapping[str, Any] | None = None,
    observed_hash: str | None = None,
) -> ProvenanceRecord:
    """Validate hash, ancestry, and external-anchor requirements for a predeclaration."""
    corpus_commits = tuple(corpus_data_commits)
    payload_hash = artifact_hash or hash_predeclaration_artifact(artifact)
    if observed_hash is not None and observed_hash != payload_hash:
        raise ValueError("predeclaration artifact hash mismatch")
    if predeclaration_commit is None or not str(predeclaration_commit).strip():
        raise ValueError("predeclaration_commit is required")
    anchor_type = None
    anchor_reference = None
    anchor_map = external_anchor or {}
    if isinstance(anchor_map, Mapping):
        anchor_type = str(anchor_map.get("anchor_type") or anchor_map.get("type") or "").strip() or None
        anchor_reference = str(anchor_map.get("anchor_reference") or anchor_map.get("reference") or "").strip() or None
    anchored = bool(anchor_type and anchor_reference)
    if not anchored:
        raise ValueError("predeclaration requires a recorded external anchor independent of the repository and clock")
    if (
        str(anchor_type).lower() in {"push_time_attestation", "remote_push", "remote-attestation"}
        and (not remote_configured or not repository_pushed)
    ):
        raise ValueError("remote push attestation requires a configured public remote and pushed repository state")
    ancestry_ok = _ancestor_check(
        str(predeclaration_commit),
        corpus_commits,
        ancestry_graph=ancestry_graph,
        timestamps=commit_timestamps,
    )
    if not ancestry_ok:
        raise ValueError("predeclaration commit is not an ancestor of all corpus-data commits")
    predeclared_before_data = ancestry_ok
    if predeclared_before_data and commit_timestamps is not None:
        predecl_time = _infer_commit_time(str(predeclaration_commit), timestamps=commit_timestamps)
        if predecl_time is not None:
            for commit in corpus_commits:
                commit_time = _infer_commit_time(commit, timestamps=commit_timestamps)
                if commit_time is not None and commit_time < predecl_time:
                    predeclared_before_data = False
                    break
    return ProvenanceRecord(
        artifact_hash=payload_hash,
        predeclaration_commit=str(predeclaration_commit),
        external_anchor_type=anchor_type,
        external_anchor_reference=anchor_reference,
        ancestry_ok=ancestry_ok,
        predeclared_before_data=predeclared_before_data,
        anchored=anchored,
        records={
            "remote_configured": remote_configured,
            "repository_pushed": repository_pushed,
            "corpus_data_commits": corpus_commits,
        },
    )


check_predeclaration_provenance = evaluate_predeclaration_provenance
validate_predeclaration_provenance = evaluate_predeclaration_provenance


def record_exclusion_entry(
    dataset_id: str,
    *,
    exclusion_type: str,
    reason: str,
    residual_use: str | None = None,
    pending: bool = False,
    cited_spec: str | None = None,
) -> ExclusionEntry:
    entry = ExclusionEntry(
        dataset_id=dataset_id,
        exclusion_type=exclusion_type,
        reason=reason,
        residual_use=residual_use,
        pending=pending,
        cited_spec=cited_spec,
    )
    reason_lower = reason.lower()
    if exclusion_type == "structural_no_change_events" and _NO_CHANGE_EVENT_SENTINEL.lower() not in reason_lower:
        raise ValueError("structural no-change exclusion must state the absence of a Change-family event")
    if exclusion_type == "commensurability_mismatch" and _COMMENSURABILITY_SENTINEL.lower() not in reason_lower:
        raise ValueError("commensurability exclusion must cite Isoprax v0.3 §5.6")
    if exclusion_type == "structural_replay_justification" and _REPLAY_JUSTIFICATION_SENTINEL.lower() not in reason_lower:
        raise ValueError("replay justification exclusion must state that deterministic replay is structurally justified")
    return entry


validate_exclusion_entry = record_exclusion_entry


def build_replay_justification_exclusion(
    dataset_id: str,
    *,
    paired_dataset_available: bool = False,
) -> ExclusionEntry:
    reason = (
        "Deterministic replay remains structurally justified because both families share one observation process; "
        "calibration does not change the conclusion. The justification is independent of paired-public-dataset scarcity "
        "and survives future large paired datasets unless that dataset also derives both families' labels from one observation process."
    )
    if paired_dataset_available:
        reason += " A later paired dataset does not rescue the exclusion unless it also shares one observation process across both families."
    return ExclusionEntry(
        dataset_id=dataset_id,
        exclusion_type="structural_replay_justification",
        reason=reason,
        residual_use="structural-conformance or baseline reference only",
        pending=False,
        cited_spec="Isoprax v0.3 §5.6",
    )


__all__ = [
    "CandidateRecord",
    "ExclusionEntry",
    "PredeclarationArtifact",
    "ProvenanceRecord",
    "ScreeningResult",
    "build_replay_justification_exclusion",
    "check_predeclaration_provenance",
    "compute_predeclaration_hash",
    "evaluate_candidate_screening",
    "evaluate_predeclaration_provenance",
    "hash_predeclaration_artifact",
    "record_exclusion_entry",
    "screen_candidate",
    "screen_candidate_system",
    "screen_candidates",
    "validate_exclusion_entry",
    "validate_predeclaration",
    "validate_predeclaration_artifact",
    "validate_predeclaration_provenance",
]
