"""Deterministic, evidence-bounded historical build qualification."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping


@dataclass(frozen=True)
class LegalCoverageRecord:
    commit: str
    reference: str
    covered: bool = True


@dataclass(frozen=True)
class RunnerDescriptor:
    immutable_identity: str
    non_root: bool
    writable_work_storage: bool


@dataclass(frozen=True)
class BuildSample:
    commits: tuple[str, ...]
    recipe_reference: str
    legal_coverage: tuple[LegalCoverageRecord, ...]
    runner: RunnerDescriptor


@dataclass(frozen=True)
class BuildPreparation:
    sample: BuildSample
    preparation_hash: str
    blocked_reason: str | None = None


@dataclass(frozen=True)
class BuildRowResult:
    commit: str
    status: str
    reason: str


@dataclass(frozen=True)
class BuildQualificationReport:
    preparation_hash: str
    rows: tuple[BuildRowResult, ...]
    measured_success_rate: float | None
    qualified: bool
    reason: str
    claim_scope: str = "build_qualification_only"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _sample_payload(sample: BuildSample) -> dict[str, Any]:
    return {
        "commits": sample.commits,
        "recipe_reference": sample.recipe_reference,
        "legal_coverage": [record.__dict__ for record in sample.legal_coverage],
        "runner": sample.runner.__dict__,
    }


def prepare_build_sample(sample: BuildSample) -> BuildPreparation:
    """Freeze inputs and block safely when preflight evidence is incomplete."""
    if not sample.commits or len(set(sample.commits)) != len(sample.commits):
        raise ValueError("sample commits must be non-empty and duplicate-free")
    if not sample.recipe_reference.strip():
        raise ValueError("recipe_reference is required")
    digest = hashlib.sha256(_canonical(_sample_payload(sample)).encode()).hexdigest()
    coverage = {record.commit: record for record in sample.legal_coverage}
    if any(
        not coverage.get(commit)
        or not coverage[commit].covered
        or not coverage[commit].reference.strip()
        for commit in sample.commits
    ):
        return BuildPreparation(sample, digest, "missing retrievable legal coverage")
    runner = sample.runner
    if (
        "@sha256:" not in runner.immutable_identity
        or not runner.non_root
        or not runner.writable_work_storage
    ):
        return BuildPreparation(
            sample, digest, "runner is not immutable, non-root, and writable"
        )
    return BuildPreparation(sample, digest)


def execute_prepared_sample(
    preparation: BuildPreparation,
    runner: Callable[[str, str, RunnerDescriptor], Mapping[str, Any]],
) -> tuple[BuildRowResult, ...]:
    """Execute only a prepared sample, retaining a terminal row for every commit."""
    if preparation.blocked_reason:
        return tuple(
            BuildRowResult(
                commit, "blocked-before-compilation", preparation.blocked_reason
            )
            for commit in preparation.sample.commits
        )
    results = []
    for commit in preparation.sample.commits:
        try:
            outcome = runner(
                commit, preparation.sample.recipe_reference, preparation.sample.runner
            )
            status = str(outcome.get("status", "blocked-before-compilation"))
            reason = str(outcome.get("reason", status))
        except Exception as error:  # injected effect boundary
            status, reason = (
                "blocked-before-compilation",
                f"runner unavailable: {error}",
            )
        if status == "success":
            results.append(BuildRowResult(commit, "success", reason))
        elif status in {"build_failed", "timeout", "interrupted", "censored"}:
            results.append(BuildRowResult(commit, "censored", reason))
        else:
            results.append(BuildRowResult(commit, "blocked-before-compilation", reason))
    return tuple(results)


def reduce_build_qualification(
    preparation: BuildPreparation,
    rows: Iterable[BuildRowResult],
    *,
    frozen_build_floor: float,
    failures_clustered: bool = False,
) -> BuildQualificationReport:
    """Qualify only a complete, executable, temporally unbiased measurement."""
    row_tuple = tuple(rows)
    expected = preparation.sample.commits
    if tuple(row.commit for row in row_tuple) != expected:
        return BuildQualificationReport(
            preparation.preparation_hash,
            row_tuple,
            None,
            False,
            "qualification unavailable: incomplete or reordered sample",
        )
    if preparation.blocked_reason or any(
        row.status == "blocked-before-compilation" for row in row_tuple
    ):
        return BuildQualificationReport(
            preparation.preparation_hash,
            row_tuple,
            None,
            False,
            "qualification unavailable: execution blocked",
        )
    rate = sum(row.status == "success" for row in row_tuple) / len(row_tuple)
    if failures_clustered:
        return BuildQualificationReport(
            preparation.preparation_hash,
            row_tuple,
            rate,
            False,
            "qualification failed: failures cluster in time",
        )
    if rate < frozen_build_floor:
        return BuildQualificationReport(
            preparation.preparation_hash,
            row_tuple,
            rate,
            False,
            "qualification failed: success rate below frozen floor",
        )
    return BuildQualificationReport(
        preparation.preparation_hash, row_tuple, rate, True, "qualified"
    )


__all__ = [
    "BuildPreparation",
    "BuildQualificationReport",
    "BuildRowResult",
    "BuildSample",
    "LegalCoverageRecord",
    "RunnerDescriptor",
    "execute_prepared_sample",
    "prepare_build_sample",
    "reduce_build_qualification",
]
