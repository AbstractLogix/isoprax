"""Deterministic replay candidate screening and predeclaration provenance.

This module stays intentionally narrow: it models the candidate screening and
plan-predeclaration checks required to keep replay work evidence-boundary-safe
without importing real-data evaluation or profile logic.
"""

from __future__ import annotations

import math
import subprocess
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from .identity import content_hash

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
_ACCEPTED_HERMETICITY_CLASSES = frozenset(
    {"pinned_distribution", "hermetic_build", "pinned_container_toolchain"}
)


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
        if (
            not isinstance(self.positive_event_thresholds, dict)
            or not self.positive_event_thresholds
        ):
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
                name: [start, end]
                for name, (start, end) in self.split_boundaries.items()
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
            raise ValueError(
                "exclusion entries must not describe a pending or deferred path"
            )
        if (
            self.exclusion_type == "structural_no_change_events"
            and _NO_CHANGE_EVENT_SENTINEL.lower() not in reason_lower
        ):
            raise ValueError(
                "structural no-change exclusion must state the absence of a Change-family event"
            )
        if (
            self.exclusion_type == "commensurability_mismatch"
            and _COMMENSURABILITY_SENTINEL.lower() not in reason_lower
        ):
            raise ValueError("commensurability exclusion must cite Isoprax v0.3 §5.6")
        if (
            self.exclusion_type == "structural_replay_justification"
            and _REPLAY_JUSTIFICATION_SENTINEL.lower() not in reason_lower
        ):
            raise ValueError(
                "replay justification exclusion must state that deterministic replay is structurally justified"
            )


def _screen_commit_supply(
    candidate: Mapping[str, Any],
    *,
    adequacy_floor: int = 0,
    positive_event_rate: float | None = None,
) -> tuple[bool, str]:
    supply = _pick(candidate, "commit_supply", "commit_capacity", default=None)
    if supply is None:
        return False, "Screen 1 failed: commit supply is missing"
    try:
        supply_value = float(supply)
    except (TypeError, ValueError):
        return False, "Screen 1 failed: commit supply is invalid"
    rate = _pick(
        candidate,
        "observed_positive_rate",
        "positive_event_rate",
        default=positive_event_rate,
    )
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
    candidate: Mapping[str, Any], *, build_floor: float
) -> tuple[bool, str]:
    success_rate = _pick(
        candidate, "sampled_build_success_rate", "build_success_rate", default=None
    )
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
        return (
            False,
            "Screen 3 failed: sampled build success rate falls below the predeclared floor",
        )
    clustered_failures = _as_bool(
        _pick(
            candidate, "build_failures_clustered", "clustered_failures", default=False
        ),
        default=False,
    )
    if clustered_failures:
        return (
            False,
            "Screen 3 failed: build failures cluster in time and would bias the corpus",
        )
    return (
        True,
        "Screen 3 passed: build success rate and temporal stability are acceptable",
    )


def derive_build_floor(
    reference_build_success_rates: Sequence[float], *, reference_project_id: str
) -> float:
    """Derive the frozen Screen 3 floor from the required reference sample."""
    if not reference_project_id.strip():
        raise ValueError("reference_project_id is required")
    if len(reference_build_success_rates) != 200:
        raise ValueError("reference sample must contain exactly 200 known-good commits")
    try:
        rates = sorted(float(rate) for rate in reference_build_success_rates)
    except (TypeError, ValueError) as error:
        raise ValueError("reference build-success rates must be numeric") from error
    if any(rate < 0.0 or rate > 1.0 for rate in rates):
        raise ValueError("reference build-success rates must be within [0.0, 1.0]")
    percentile_index = math.floor(0.05 * (len(rates) - 1))
    return min(math.floor(rates[percentile_index] * 100) / 100, 0.90)


def _screen_prediction_metadata(
    candidate: Mapping[str, Any], *, prediction_time_feature_allowlist: frozenset[str]
) -> tuple[bool, str]:
    samples = _pick(
        candidate, "sampled_prediction_fields", "prediction_time_field_samples"
    )
    if not isinstance(samples, Mapping) or not samples:
        return False, "Screen 4 failed: sampled prediction-time fields are required"
    for commit, fields in samples.items():
        if not str(commit).strip():
            return False, "Screen 4 failed: sampled commit identifier is required"
        field_names = set(fields.keys()) if isinstance(fields, Mapping) else set(fields)
        if not field_names.issubset(prediction_time_feature_allowlist):
            return (
                False,
                "Screen 4 failed: prediction-time feature allowlist cannot be populated at sampled commits",
            )
    if not prediction_time_feature_allowlist:
        return (
            False,
            "Screen 4 failed: prediction-time feature allowlist cannot be populated at sampled commits",
        )
    return True, "Screen 4 passed: prediction-time feature allowlist is populatable"


def _screen_estimated_buildable_window(
    candidate: Mapping[str, Any], *, adequacy_floor: int
) -> tuple[bool, str]:
    window = _pick(
        candidate,
        "estimated_buildable_window_commits",
        "estimated_recent_buildable_window_commits",
    )
    if window is None:
        return False, "Screen 1 failed: estimated recent buildable window is missing"
    candidate_with_window = dict(candidate)
    candidate_with_window["commit_supply"] = window
    passed, _ = _screen_commit_supply(
        candidate_with_window, adequacy_floor=adequacy_floor
    )
    if not passed:
        return (
            False,
            "Screen 1 failed: estimated recent buildable window cannot support the adequacy floor",
        )
    return (
        True,
        "Screen 1 passed: estimated recent buildable window supports the adequacy floor",
    )


def _screen_governing_legal_terms(
    candidate: Mapping[str, Any],
) -> tuple[bool, str, Mapping[str, Any] | None]:
    instruments = _pick(candidate, "legal_instruments", "terms_instruments", default=())
    if not isinstance(instruments, Sequence) or isinstance(instruments, (str, bytes)):
        return False, "Screen 2 failed: legal instruments are required", None
    governing = [
        item
        for item in instruments
        if isinstance(item, Mapping)
        and item.get("governs_source_built_artifact") is True
    ]
    if len(governing) != 1:
        return (
            False,
            "Screen 2 failed: exactly one governing source-built legal instrument is required",
            None,
        )
    instrument = governing[0]
    if (
        not str(instrument.get("instrument_type", "")).strip()
        or not str(instrument.get("reference", "")).strip()
    ):
        return (
            False,
            "Screen 2 failed: governing legal instrument requires type and retrievable reference",
            None,
        )
    if _as_bool(instrument.get("forbids_publication")) or _as_bool(
        instrument.get("forbids_redistribution")
    ):
        return (
            False,
            "Screen 2 failed: governing legal instrument forbids benchmark publication or derived-metric redistribution",
            instrument,
        )
    return (
        True,
        "Screen 2 passed: governing legal instrument permits the intended use",
        instrument,
    )


def _screen_replay_readiness(
    candidate: Mapping[str, Any],
) -> tuple[bool, str, str | None]:
    evidence = _pick(
        candidate, "replay_readiness_evidence", "hermeticity_evidence", default={}
    )
    if not isinstance(evidence, Mapping):
        return False, "Screen 2.5 failed: replay-readiness evidence is required", None
    hermeticity_class = str(evidence.get("hermeticity_class", "")).strip()
    if hermeticity_class not in _ACCEPTED_HERMETICITY_CLASSES:
        return (
            False,
            "Screen 2.5 failed: an accepted hermeticity class is required",
            None,
        )
    if not str(evidence.get("evidence_reference", "")).strip():
        return (
            False,
            "Screen 2.5 failed: hermeticity evidence reference is required",
            None,
        )
    return (
        True,
        "Screen 2.5 passed: replay-readiness evidence is accepted",
        hermeticity_class,
    )


def screen_early_candidate(
    candidate: Any,
    *,
    adequacy_floor: int,
    prediction_time_feature_allowlist: Iterable[str],
) -> CandidateRecord:
    """Screen early eligibility without executing or interpreting historical builds."""
    candidate_map = _coerce_mapping(candidate)
    system_id = str(
        _pick(candidate_map, "system_id", "candidate_id", default="candidate")
    ).strip()
    allowlist = frozenset(
        str(field) for field in prediction_time_feature_allowlist if str(field).strip()
    )
    results: list[ScreeningResult] = []
    governing_instrument: Mapping[str, Any] | None = None
    hermeticity_class: str | None = None
    screen_calls = (
        (
            "estimated_buildable_window",
            lambda: _screen_estimated_buildable_window(
                candidate_map, adequacy_floor=adequacy_floor
            ),
        ),
        ("governing_legal_terms", lambda: _screen_governing_legal_terms(candidate_map)),
        ("replay_readiness", lambda: _screen_replay_readiness(candidate_map)),
        (
            "prediction_metadata",
            lambda: _screen_prediction_metadata(
                candidate_map, prediction_time_feature_allowlist=allowlist
            ),
        ),
    )
    for index, (name, check) in enumerate(screen_calls, start=1):
        result = check()
        passed, detail = result[:2]
        if name == "governing_legal_terms":
            governing_instrument = result[2]
        if name == "replay_readiness":
            hermeticity_class = result[2]
        results.append(ScreeningResult(name, index, passed, detail))
        if not passed:
            metadata: dict[str, Any] = {"adequacy_floor": adequacy_floor}
            if governing_instrument is not None:
                metadata["governing_legal_instrument"] = dict(governing_instrument)
            return CandidateRecord(system_id, False, name, tuple(results), metadata)
    return CandidateRecord(
        system_id,
        True,
        None,
        tuple(results),
        {
            "adequacy_floor": adequacy_floor,
            "governing_legal_instrument": dict(governing_instrument or {}),
            "hermeticity_class": hermeticity_class,
            "historical_build_rate_qualification": "deferred_to_replay_environment",
            "prediction_time_feature_allowlist": tuple(sorted(allowlist)),
        },
    )


def _order_screen_results(
    candidate: Mapping[str, Any],
    *,
    adequacy_floor: int,
    build_floor: float,
    prediction_time_feature_allowlist: frozenset[str],
) -> list[ScreeningResult]:
    screens = (
        (
            "commit_supply",
            _screen_commit_supply(candidate, adequacy_floor=adequacy_floor),
        ),
        ("licence_terms", _screen_licence_terms(candidate)),
        ("build_rate", _screen_build_rate(candidate, build_floor=build_floor)),
        (
            "prediction_metadata",
            _screen_prediction_metadata(
                candidate,
                prediction_time_feature_allowlist=prediction_time_feature_allowlist,
            ),
        ),
    )
    results: list[ScreeningResult] = []
    for index, (name, (passed, detail)) in enumerate(screens, start=1):
        results.append(
            ScreeningResult(
                screen_name=name, screen_number=index, passed=passed, detail=detail
            )
        )
        if not passed:
            break
    return results


def screen_candidate(
    candidate: Any,
    *,
    adequacy_floor: int,
    reference_build_success_rates: Sequence[float],
    reference_project_id: str,
    prediction_time_feature_allowlist: Iterable[str],
) -> CandidateRecord:
    """Screen one candidate system in the required fixed order."""
    candidate_map = _coerce_mapping(candidate)
    system_id = str(
        _pick(candidate_map, "system_id", "candidate_id", default="candidate")
    ).strip()
    if system_id == reference_project_id:
        raise ValueError("reference project must be unrelated to the candidate")
    allowlist = frozenset(
        str(field) for field in prediction_time_feature_allowlist if str(field).strip()
    )
    build_floor = derive_build_floor(
        reference_build_success_rates, reference_project_id=reference_project_id
    )
    results = _order_screen_results(
        candidate_map,
        adequacy_floor=adequacy_floor,
        build_floor=build_floor,
        prediction_time_feature_allowlist=allowlist,
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
                "reference_project_id": reference_project_id,
                "prediction_time_feature_allowlist": tuple(sorted(allowlist)),
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
            "reference_project_id": reference_project_id,
            "prediction_time_feature_allowlist": tuple(sorted(allowlist)),
        },
    )


def screen_candidates(
    candidates: Iterable[Any],
    *,
    adequacy_floor: int,
    reference_build_success_rates: Sequence[float],
    reference_project_id: str,
    prediction_time_feature_allowlist: Iterable[str],
) -> tuple[CandidateRecord, ...]:
    """Return a record for every candidate considered, preserving screen order."""
    return tuple(
        screen_candidate(
            candidate,
            adequacy_floor=adequacy_floor,
            reference_build_success_rates=reference_build_success_rates,
            reference_project_id=reference_project_id,
            prediction_time_feature_allowlist=prediction_time_feature_allowlist,
        )
        for candidate in candidates
    )


def evaluate_candidate_screening(
    candidates: Iterable[Any],
    *,
    adequacy_floor: int,
    reference_build_success_rates: Sequence[float],
    reference_project_id: str,
    prediction_time_feature_allowlist: Iterable[str],
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
        reference_build_success_rates=reference_build_success_rates,
        reference_project_id=reference_project_id,
        prediction_time_feature_allowlist=prediction_time_feature_allowlist,
    )


def screen_candidate_system(
    candidate: Any,
    *,
    adequacy_floor: int,
    reference_build_success_rates: Sequence[float],
    reference_project_id: str,
    prediction_time_feature_allowlist: Iterable[str],
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
        reference_build_success_rates=reference_build_success_rates,
        reference_project_id=reference_project_id,
        prediction_time_feature_allowlist=prediction_time_feature_allowlist,
    )


def hash_predeclaration_artifact(
    artifact: PredeclarationArtifact | Mapping[str, Any],
) -> str:
    payload = (
        artifact.to_dict()
        if isinstance(artifact, PredeclarationArtifact)
        else dict(artifact)
    )
    return content_hash(payload)


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
                    raise ValueError(
                        f"split_boundaries[{name}] must contain exactly two values"
                    )
                split_boundaries[name] = (str(value[0]), str(value[1]))
                continue
            raise ValueError(f"split_boundaries[{name}] must be a sequence or mapping")
        artifact_obj = PredeclarationArtifact(
            artifact_id=str(artifact.get("artifact_id", "artifact")),
            content=str(artifact.get("content", "")),
            soak_duration=str(artifact.get("soak_duration", "")),
            soak_duration_rule=str(artifact.get("soak_duration_rule", "")),
            positive_event_definition=str(
                artifact.get("positive_event_definition", "")
            ),
            positive_event_thresholds=dict(
                artifact.get("positive_event_thresholds", {})
            ),
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
    if (
        observation_window is not None
        and "observation" in rule
        and "training" not in rule
    ):
        raise ValueError(
            "soak duration must be derived from training-period-only data, not the observation window"
        )
    if "observation window" in rule and "training" not in rule:
        raise ValueError(
            "soak duration rule cannot use the observation window it bounds"
        )
    return True


validate_predeclaration = validate_predeclaration_artifact


def _infer_commit_time(
    commit: str, *, timestamps: Mapping[str, Any] | None = None
) -> datetime | None:
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
    repository_path: str | Path | None,
    git_runner: Callable[[Sequence[str], str | Path], bool] | None = None,
) -> bool:
    if not predeclaration_commit:
        return False
    corpora = tuple(corpus_data_commits)
    if not corpora:
        return True
    if repository_path is None:
        raise ValueError("repository_path is required to execute Git ancestry checks")
    runner = git_runner or _run_git_ancestor_check
    for commit in corpora:
        if not runner(
            ("git", "merge-base", "--is-ancestor", predeclaration_commit, commit),
            repository_path,
        ):
            return False
    return True


def _run_git_ancestor_check(
    command: Sequence[str], repository_path: str | Path
) -> bool:
    return (
        subprocess.run(
            command,
            cwd=repository_path,
            check=False,
            capture_output=True,
            text=True,
        ).returncode
        == 0
    )


def evaluate_predeclaration_provenance(
    artifact: PredeclarationArtifact | Mapping[str, Any],
    *,
    artifact_hash: str | None = None,
    predeclaration_commit: str | None = None,
    corpus_data_commits: Iterable[str] = (),
    external_anchor: Mapping[str, Any] | None = None,
    remote_configured: bool = False,
    repository_pushed: bool = False,
    repository_path: str | Path | None = None,
    git_runner: Callable[[Sequence[str], str | Path], bool] | None = None,
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
        anchor_type = (
            str(anchor_map.get("anchor_type") or anchor_map.get("type") or "").strip()
            or None
        )
        anchor_reference = (
            str(
                anchor_map.get("anchor_reference") or anchor_map.get("reference") or ""
            ).strip()
            or None
        )
    anchored = bool(anchor_type and anchor_reference)
    if not anchored:
        raise ValueError(
            "predeclaration requires a recorded external anchor independent of the repository and clock"
        )
    if anchor_map.get("independent_of_repository_and_clock") is not True:
        raise ValueError(
            "external anchor must be independent of the project repository and clock"
        )
    if str(anchor_type).lower() in {
        "push_time_attestation",
        "remote_push",
        "remote-attestation",
    } and (not remote_configured or not repository_pushed):
        raise ValueError(
            "remote push attestation requires a configured public remote and pushed repository state"
        )
    ancestry_ok = _ancestor_check(
        str(predeclaration_commit),
        corpus_commits,
        repository_path=repository_path,
        git_runner=git_runner,
    )
    if not ancestry_ok:
        raise ValueError(
            "predeclaration commit is not an ancestor of all corpus-data commits"
        )
    predeclared_before_data = ancestry_ok
    if predeclared_before_data and commit_timestamps is not None:
        predecl_time = _infer_commit_time(
            str(predeclaration_commit), timestamps=commit_timestamps
        )
        if predecl_time is not None:
            for commit in corpus_commits:
                commit_time = _infer_commit_time(commit, timestamps=commit_timestamps)
                if commit_time is not None and commit_time < predecl_time:
                    raise ValueError(
                        "corpus-data commit predates the anchored predeclaration commit"
                    )
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
    if (
        exclusion_type == "structural_no_change_events"
        and _NO_CHANGE_EVENT_SENTINEL.lower() not in reason_lower
    ):
        raise ValueError(
            "structural no-change exclusion must state the absence of a Change-family event"
        )
    if (
        exclusion_type == "commensurability_mismatch"
        and _COMMENSURABILITY_SENTINEL.lower() not in reason_lower
    ):
        raise ValueError("commensurability exclusion must cite Isoprax v0.3 §5.6")
    if (
        exclusion_type == "structural_replay_justification"
        and _REPLAY_JUSTIFICATION_SENTINEL.lower() not in reason_lower
    ):
        raise ValueError(
            "replay justification exclusion must state that deterministic replay is structurally justified"
        )
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
    "derive_build_floor",
    "evaluate_candidate_screening",
    "evaluate_predeclaration_provenance",
    "hash_predeclaration_artifact",
    "record_exclusion_entry",
    "screen_candidate",
    "screen_early_candidate",
    "screen_candidate_system",
    "screen_candidates",
    "validate_exclusion_entry",
    "validate_predeclaration",
    "validate_predeclaration_artifact",
    "validate_predeclaration_provenance",
]
