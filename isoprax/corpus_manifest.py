"""Deterministic publishable manifest helpers for replayable corpora.

This module provides the thin, offline scaffolding described in the Stage 1
roadmap: manifest-first provenance for admitted corpora without escalating claim
status. It intentionally stays behind the Stage 1 admission gate and does not
import real-data model or profile logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .admission import AdmissionProfile, CorpusRow, SplitDefinition

_CANONICAL_SPLITS = ("train", "calibration_fit", "calibration_gate", "test")


@dataclass(frozen=True)
class CorpusManifest:
    """Publishable summary for a candidate corpus.

    This is intentionally minimal: it captures the metadata needed for a reader to
    reproduce split definitions, counts, and admissibility review without relying
    on runtime state or hidden defaults.
    """

    source_system: str
    release_scope: str
    horizon_rule: str
    thresholds_frozen: bool
    split_definitions: tuple[SplitDefinition, ...]
    counts_by_split: dict[str, dict[str, int]]
    expected_system_id: str | None = None
    published_artifacts: tuple[str, ...] = ()
    privacy_constraints: tuple[str, ...] = ()
    generated_by: str = "isoprax.corpus_manifest"

    def __post_init__(self) -> None:
        if not self.source_system.strip():
            raise ValueError("source_system is required")
        if not self.release_scope.strip():
            raise ValueError("release_scope metadata is required")
        if not self.horizon_rule.strip():
            raise ValueError("horizon_rule metadata is required")
        if not self.split_definitions:
            raise ValueError("split_definitions are required")
        if set(self.counts_by_split) != set(_CANONICAL_SPLITS):
            raise ValueError("counts_by_split must include canonical splits")
        for split in _CANONICAL_SPLITS:
            counts = self.counts_by_split.get(split, {})
            for outcome in ("observed_positive", "observed_negative", "censored"):
                if outcome not in counts:
                    raise ValueError(f"missing count for {split}:{outcome}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_system": self.source_system,
            "release_scope": self.release_scope,
            "horizon_rule": self.horizon_rule,
            "thresholds_frozen": self.thresholds_frozen,
            "split_definitions": [
                {"name": s.name, "start": s.start, "end": s.end}
                for s in self.split_definitions
            ],
            "counts_by_split": self.counts_by_split,
            "expected_system_id": self.expected_system_id,
            "published_artifacts": list(self.published_artifacts),
            "privacy_constraints": list(self.privacy_constraints),
            "generated_by": self.generated_by,
        }


def _counts_by_split(rows: list[CorpusRow]) -> dict[str, dict[str, int]]:
    counts = {
        split: {
            "observed_positive": 0,
            "observed_negative": 0,
            "censored": 0,
        }
        for split in _CANONICAL_SPLITS
    }
    for row in rows:
        split = row.split
        if split not in counts:
            continue
        counts[split][row.outcome_class] += 1
    return counts


def build_corpus_manifest(
    rows: list[CorpusRow],
    profile: AdmissionProfile,
    *,
    source_system: str,
    release_scope: str | None = None,
    published_artifacts: tuple[str, ...] = (),
    privacy_constraints: tuple[str, ...] = (),
    generated_by: str = "isoprax.corpus_manifest",
) -> CorpusManifest:
    """Build a publishable manifest from rows + a deterministic admission profile."""

    if not source_system or not source_system.strip():
        raise ValueError("source_system is required")
    manifest_release_scope = release_scope if release_scope is not None else profile.release_scope
    if not manifest_release_scope.strip():
        raise ValueError("release_scope metadata is required")

    return CorpusManifest(
        source_system=source_system,
        release_scope=manifest_release_scope,
        horizon_rule=profile.horizon_rule,
        thresholds_frozen=profile.thresholds_frozen,
        split_definitions=profile.split_definitions,
        counts_by_split=_counts_by_split(sorted(rows, key=lambda r: r.row_id)),
        expected_system_id=profile.expected_system_id,
        published_artifacts=tuple(published_artifacts),
        privacy_constraints=tuple(privacy_constraints),
        generated_by=generated_by,
    )


def validate_corpus_manifest(manifest: Mapping[str, Any]) -> bool:
    """Validate a manifest dict or manifest dataclass.

    Returns True when the manifest has the deterministic metadata required for
    reproducible, publishable corpus review.
    """

    if isinstance(manifest, CorpusManifest):
        return True

    if not isinstance(manifest, Mapping):
        raise TypeError("manifest must be a mapping or CorpusManifest")

    required = {
        "source_system",
        "release_scope",
        "horizon_rule",
        "thresholds_frozen",
        "split_definitions",
        "counts_by_split",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise ValueError(f"manifest missing required fields: {missing}")

    if not str(manifest["source_system"]).strip():
        raise ValueError("source_system is required")
    if not str(manifest["release_scope"]).strip():
        raise ValueError("release_scope metadata is required")
    if not str(manifest["horizon_rule"]).strip():
        raise ValueError("horizon_rule metadata is required")
    if not isinstance(manifest["split_definitions"], (list, tuple)):
        raise ValueError("split_definitions must be list-like")
    if not isinstance(manifest["counts_by_split"], Mapping):
        raise ValueError("counts_by_split must be a mapping")
    if set(manifest["counts_by_split"]) != set(_CANONICAL_SPLITS):
        raise ValueError("counts_by_split must include canonical splits")
    return True
