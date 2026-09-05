# Implementation Plan: Stage 1 Corpus Admission and Replay Evidence

**Branch**: `002-stage1-corpus-admission` | **Date**: 2026-09-05 | **Spec**: [spec.md](spec.md)

## Summary

Implement a deterministic admission gate for paired-corpus evidence that
validates lineage integrity, censoring rules, prediction-time leakage control,
frozen chronological splits, adequacy thresholds, and claim-discipline outputs.
Reuse compatible archived decisions; keep JEPA/profile implementation out
of scope.

## Technical Context

**Language/Version**: Python >=3.10,<3.15

**Primary Dependencies**: Existing `isoprax` core; optional tabular utilities as
needed for admission checks

**Storage**: Local files/manifests and existing SQLite-capable interfaces where
appropriate

**Testing**: pytest + focused admission conformance tests

**Target Platform**: Offline/local developer environment

**Project Type**: Library extension and conformance test expansion

**Constraints**: No conformance auto-promotion; no private-data dependency;
must preserve Stage 0 claim boundaries

## Constitution Check

- Specification Authority: pass — Isoprax spec remains authoritative.
- Honest Conformance: pass — admission is not a conformance upgrade.
- Contract-First Testing: pass — each admission gate requires explicit tests.
- Deterministic Core: pass — identical inputs must produce identical outputs.
- Minimal Reference Scope: pass — archive reuse limited to admission/research
  hygiene constraints.

## Project Structure

### Documentation

```text
specs/002-stage1-corpus-admission/
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── plan.md
├── tasks.md
└── contracts/library-contract.md
```

### Source impact (planned)

```text
isoprax/
├── (new) admission.py
├── (optional) corpus_manifest.py
└── (optional) replay_constraints.py
tests/
└── (new) test_stage1_admission.py
```

## Complexity Tracking

No constitution violations expected. Any pressure to import JEPA/profile logic
must be rejected or moved to a separate feature specification.
