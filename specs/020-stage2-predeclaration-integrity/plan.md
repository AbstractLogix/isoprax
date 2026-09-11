# Implementation Plan: Stage 2 Predeclaration Integrity

Validate the canonical JSON artifact hash with its self-hash field omitted,
derive and verify the artifact's introducing Git commit, and pass those values
through `evaluate_predeclaration_provenance`. Preserve the anchor as
unverified until an independent verifier is available, and emit an explicit
inconclusive result instead of a feasibility report. Replace hardcoded outcome
semantics in the whoami script with structured predeclared fields.

Validation includes tamper rejection, provenance verification, declared-field
construction, the real pilot command, full pytest, and Ruff.
