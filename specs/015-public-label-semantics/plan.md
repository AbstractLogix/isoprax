# Implementation Plan: Public Label-Semantics and Split-Sensitivity Evidence

**Branch**: `codex/015-public-label-semantics` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

## Summary

Extend the existing offline public-label evidence seam with structured label
records, procedure metadata, graded semantic comparisons, and a deterministic
fail-closed report. Reuse existing structured `OutcomeDefinition` values and
`PublicLabelEvidenceManifest` provenance checks. Do not add network retrieval,
model training, corpus admission, or semantic conformance claims.

## Technical Context

**Language/Version**: Python 3.10–3.14

**Dependencies**: Existing standard library and Isoprax domain types; no new runtime dependency

**Storage**: Immutable dataclasses and JSON-like deterministic report values; no database changes

**Testing**: Focused pytest module, Ruff, existing full test and coverage gate

**Target**: Offline Linux/WSL and CI

**Constraints**: Preserve existing public-label API, fail closed, keep evidence distinct from conformance

## Constitution Check

| Principle | Design response | Result |
| --- | --- | --- |
| Specification Authority | New behavior is documented in Feature 015 and uses existing structured domain contracts. | Pass |
| Honest Conformance | Reports explicitly remain public-label evidence only. | Pass |
| Contract-First Testing | Valid, blocked, inconclusive, bridgeable, irreducible, and malformed paths receive focused tests. | Pass |
| Deterministic Core | Pure dataclass reduction with sorted identifiers and no network access. | Pass |
| Minimal Reference Scope | One extension module/seam; no adapters or model pipeline. | Pass |

## Project Structure

```text
isoprax/public_label_evidence.py   # structured records, comparison, report reducer
isoprax/__init__.py                # public exports
tests/test_public_label_evidence.py# focused contract tests
examples/public-label-evidence/    # supplied manifest shape and claim boundary
```

## Implementation approach

1. Add typed procedure metadata and label-definition records with explicit
   unknown values and validation.
2. Compare structured outcome definitions by stable dimensions, classify
   direct/bridgeable/irreducible/unavailable, and require bridge evidence.
3. Build a sorted report that retains source reducer status and never grants a
   pooling or semantic-equivalence permission.
4. Preserve the existing manifest reducer and add exports, fixture documentation,
   and focused tests.

## Complexity Tracking

No constitution exceptions or new dependencies are required.
