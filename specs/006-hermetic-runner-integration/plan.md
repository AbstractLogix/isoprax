# Implementation Plan: Hermetic Runner Integration

**Branch**: `006-hermetic-runner-integration` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

## Summary

Add a small, deterministic execution-evidence module that validates a fully predeclared runner configuration, delegates the sole effect to an injected backend, hashes retained declared artifacts, and maps terminal outcomes to existing build-evidence statuses. It extends feature 005 without choosing or provisioning a container engine.

## Technical Context

**Language/Version**: Python >=3.10,<3.15
**Primary Dependencies**: standard library; existing `build_qualification` records
**Storage**: immutable dataclasses and canonical JSON/content hashes; caller-owned artifact storage
**Testing**: pytest focused conformance tests
**Target Platform**: offline local library; injected runner backend
**Project Type**: library
**Performance Goals**: deterministic validation and evidence reduction; no target throughput claim
**Constraints**: no network, engine provisioning, mutable dependency retrieval, direct qualification decision, or conformance upgrade
**Scale/Scope**: one configured execution attempt per prepared revision and its declared output paths

## Constitution Check

- **Specification Authority**: Pass. The design blocks missing containment controls and preserves feature 005 provenance.
- **Honest Conformance**: Pass. The only public result is execution evidence; it cannot emit qualification, admission, or conformance claims.
- **Contract-First Testing**: Pass. Focused tests map to FR-001 through FR-009, including all blocking and censored paths.
- **Deterministic Core, Explicit Effects**: Pass. Canonical validation, identity derivation, classification, and artifact hashing are pure; the backend is the only injected effect.
- **Minimal Reference Scope**: Pass. No container SDK, registry, source retrieval, or telemetry adapter is introduced.

## Project Structure

### Documentation

```text
specs/006-hermetic-runner-integration/
├── spec.md
├── research.md
├── data-model.md
├── contracts/runner-backend.md
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
└── __init__.py

tests/
├── test_build_qualification.py
└── test_hermetic_runner.py
```

**Structure Decision**: Add one library module beside the existing feature 005 contract, export its public records from `isoprax.__init__`, and keep its backend fixture-based in focused tests.

## Complexity Tracking

No constitutional violations or extra architecture are required.
