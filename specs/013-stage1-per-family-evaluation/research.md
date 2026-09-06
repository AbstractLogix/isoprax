# Research: Stage 1 Per-Family Evaluation

## Decision: Build per-family evaluation as a deterministic reducer

**Rationale**: The repository already has deterministic admission gating and
calibration primitives. This feature needs a narrow composition layer that
consumes admitted rows and produces one family-scoped evidence report.

**Alternatives considered**:

- Extend cross-family reporting directly in `evaluation.py` (rejected: blurs
  non-pooling boundary and feature scope).
- Recompute admission gates during evaluation (rejected: duplicates authority
  and risks inconsistent outcomes).

## Decision: Make non-admission and missing evidence first-class statuses

**Rationale**: Requirements call for fail-closed behavior and explicit
inconclusive reporting when required calibration/test evidence is missing.

**Alternatives considered**:

- Single pass/fail status (rejected: hides distinction between blocked and
  incomplete evidence).
- Silent defaults for missing calibration evidence (rejected: violates explicit
  evidence discipline).

## Decision: Keep claim boundary immutable and below Semantic/Full

**Rationale**: Constitution principle II requires honest conformance claims.
Per-family outputs are evidentiary only and must never be interpreted as
semantic/full conformance or efficacy.

**Alternatives considered**:

- Emit “calibrated => stronger claim” language (rejected: calibration does not
  imply semantic comparability or efficacy).

## Implementation constraints carried forward

- One admitted corpus and one family per evaluation run.
- Predeclared threshold version and score field are mandatory.
- Split isolation is mandatory (`calibration_fit`, `calibration_gate`, `test`).
- Determinism is guaranteed by canonical sorting and hashing.
