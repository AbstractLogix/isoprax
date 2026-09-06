# Implementation Plan: Replay Observation Capture

**Branch**: `007-replay-observation-capture` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

## Summary

Add one deterministic replay-capture module that accepts a fully frozen one-service lane definition and feature 005/006 evidence, delegates deployment and observation effects to an injected backend, then retains one immutable terminal record. The module fail-closes on incomplete predeclaration, lineage, attribution, or allowed-evidence checks; it maps build/deployment/telemetry failures to censored evidence and makes no admission or conformance decision.

## Technical Context

**Language/Version**: Python >=3.10,<3.15
**Primary Dependencies**: standard library; existing `build_qualification` and `hermetic_runner` records
**Storage**: immutable dataclasses, canonical JSON, and SHA-256 identities; caller-owned deployment and telemetry evidence storage
**Testing**: pytest focused conformance tests
**Target Platform**: offline local library with an injected replay-capture backend
**Project Type**: library
**Performance Goals**: deterministic validation and evidence reduction; no throughput claim
**Constraints**: no network or production-data acquisition in the core; one system/service/revision per lane; no mutable workload, horizon, threshold, or schema; no admission, evaluation, or conformance upgrade
**Scale/Scope**: one terminal capture record per requested replay lane, with zero or more content-identified retained observation artifacts

## Constitution Check

- **Specification Authority**: Pass. The design preserves the Stage 1 lineage, score-time, censoring, and single-system boundaries from feature 002 and the execution-evidence boundary from feature 006.
- **Honest Conformance**: Pass. Outputs are explicitly replay-observation evidence only; no corpus-admission, model-performance, Semantic, or Full Conformance claim is possible.
- **Contract-First Testing**: Pass. Focused tests will trace FR-001 through FR-011, including blocked, censored, privacy, attribution, and identity-change paths.
- **Deterministic Core, Explicit Effects**: Pass. Validation, lineage binding, identity derivation, evidence hashing, and terminal classification are pure. The injected backend is the only deployment/observation effect boundary.
- **Minimal Reference Scope**: Pass. No deployment engine, telemetry SDK, source retrieval, private data integration, or corpus assembly is introduced.

## Project Structure

### Documentation

```text
specs/007-replay-observation-capture/
├── spec.md
├── research.md
├── data-model.md
├── contracts/replay-capture-backend.md
├── quickstart.md
├── plan.md
├── tasks.md
└── converge.md
```

### Source Code

```text
isoprax/
├── build_qualification.py
├── hermetic_runner.py
├── replay_capture.py
└── __init__.py

tests/
├── test_build_qualification.py
├── test_hermetic_runner.py
└── test_replay_capture.py
```

**Structure Decision**: Add a single `replay_capture` module beside the existing deterministic evidence modules. It consumes their public immutable records, exposes its records from `isoprax.__init__`, and uses fixture-based injected backends in a focused test file.

## Complexity Tracking

No constitutional violations or extra architecture are required.
