"""Compatibility wrapper for replay predeclaration logic."""

from .replay_selection import (
    ExclusionEntry,
    PredeclarationArtifact,
    ProvenanceRecord,
    build_replay_justification_exclusion,
    check_predeclaration_provenance,
    compute_predeclaration_hash,
    evaluate_predeclaration_provenance,
    hash_predeclaration_artifact,
    record_exclusion_entry,
    validate_exclusion_entry,
    validate_predeclaration,
    validate_predeclaration_artifact,
    validate_predeclaration_provenance,
)

__all__ = [
    "ExclusionEntry",
    "PredeclarationArtifact",
    "ProvenanceRecord",
    "build_replay_justification_exclusion",
    "check_predeclaration_provenance",
    "compute_predeclaration_hash",
    "evaluate_predeclaration_provenance",
    "hash_predeclaration_artifact",
    "record_exclusion_entry",
    "validate_exclusion_entry",
    "validate_predeclaration",
    "validate_predeclaration_artifact",
    "validate_predeclaration_provenance",
]
