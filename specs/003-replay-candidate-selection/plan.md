# Implementation Plan: Replay Candidate Selection and Predeclaration

**Branch**: `003-replay-candidate-selection` | **Date**: 2026-09-05 | **Spec**: [spec.md](spec.md)

## Summary

Implement a narrow evidence-boundary layer that screens candidate systems deterministically and records a tamper-evident analysis-plan predeclaration before any Stage 1 corpus data is admitted. Keep the implementation offline, deterministic, and strictly outside actual corpus collection or model evaluation.

## Technical Context

**Language/Version**: Python >=3.10,<3.15

**Primary Dependencies**: Existing `isoprax` core, standard library hashing, and local Git metadata where available

**Storage**: Dataclass-based records and serialized artifact metadata

**Testing**: pytest + focused screening, provenance, and exclusion tests

**Target Platform**: Offline/local developer environment

**Project Type**: Library extension plus deterministic conformance support

**Constraints**: No JEPA/profile imports; no corpus-collection logic; no conformance-class upgrades.

## Constitution Check

- Specification Authority: pass — the repository's Stage 0 and Stage 1 guidance remain authoritative.
- Honest Conformance: pass — screening and predeclaration remain evidence plumbing only.
- Contract-First Testing: pass — each screen, hash check, and exclusion entry requires explicit tests.
- Deterministic Core: pass — identical inputs must produce identical outputs.
- Minimal Reference Scope: pass — archive reuse limited to screening and provenance hygiene.

## Project Structure

```text
specs/003-replay-candidate-selection/
├── spec.md
├── plan.md
├── tasks.md
├── quickstart.md
└── checklists/
    └── requirements.md
```

### Source impact (planned)

```text
isoprax/
├── (new) replay_selection.py
├── (new) predeclaration.py
├── (new) candidate_selection.py
└── __init__.py (exports)

tests/
└── (new) test_replay_selection.py
```

## Complexity Tracking

No constitution violations are expected. If a future implementation is tempted to import model-evaluation or JEPA/profile logic, that work must be moved to a separate specification.
