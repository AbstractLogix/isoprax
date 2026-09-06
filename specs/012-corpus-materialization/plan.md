# Implementation Plan: Reproducible Public Corpus Materialization

**Branch**: `012-corpus-materialization` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/012-corpus-materialization/spec.md`

## Summary

Implement deterministic, offline materialization of a public-only corpus artifact
from accepted assembly evidence. The feature must preserve original outcome and
lineage fields, produce stable hashes and ordering, explicitly represent withheld
or unavailable evidence, and fail closed for private/privileged/profile-mismatch
inputs without escalating conformance claims.

## Technical Context

**Language/Version**: Python >=3.10,<3.15

**Primary Dependencies**: Standard library (`dataclasses`, `hashlib`, `json`), existing `isoprax` modules (`corpus_assembly`, `corpus_manifest`, `public_observation`)

**Storage**: Local files/manifests only (no network access)

**Testing**: `pytest` with branch-aware coverage via `pytest-cov`

**Target Platform**: Linux/macOS local developer environment and CI

**Project Type**: Deterministic library module + conformance tests

**Performance Goals**: Deterministic output identity; stable ordering for equivalent input sets

**Constraints**: Offline-only behavior, fail-closed rejection paths, no outcome recomputation, no conformance class escalation

**Scale/Scope**: Stage 1 synthetic/public evidence pathways for one frozen profile per materialization run

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Specification Authority**: Pass — requirements map directly to Feature 012 scope.
- **Honest Conformance**: Pass — outputs are evidence artifacts only; no Semantic/Full claims.
- **Contract-First Testing**: Pass — deterministic/hash and rejection paths are test-first targets.
- **Deterministic Core, Explicit Effects**: Pass — pure input normalization and hashing with no network dependency.
- **Minimal Reference Scope**: Pass — reuse only current repository Stage 0/Stage 1 evidence helpers.

Post-design re-check: **Pass**; no additional principle exceptions introduced.

## Project Structure

### Documentation (this feature)

```text
specs/012-corpus-materialization/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── library-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
isoprax/
├── corpus_assembly.py
├── corpus_manifest.py
├── (new) public_corpus.py
└── __init__.py

tests/
├── test_corpus_assembly.py
├── test_corpus_manifest.py
└── (new) test_public_corpus.py
```

**Structure Decision**: Extend the existing library-oriented module layout and
add a dedicated `public_corpus.py` seam for deterministic materialization logic,
keeping adapters and external IO out of scope.

## Complexity Tracking

No constitution violations expected for this feature.
