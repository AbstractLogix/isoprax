# Implementation Plan: Replay Corpus Assembly

**Branch**: 008-corpus-assembly | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

## Summary

Add a deterministic corpus-assembly module that converts immutable replay-capture records and caller-supplied score-time fields into existing Stage 1 CorpusRow records plus a bounded assembly report. The module validates a frozen profile before reduction, preserves censoring, and delegates final admission to the existing admission gate.

## Technical Context

**Language/Version**: Python >=3.10,<3.15
**Primary Dependencies**: standard library; existing admission, corpus manifest, and replay capture records
**Storage**: immutable dataclasses and canonical JSON/SHA-256 identities; caller-owned evidence storage
**Testing**: pytest focused conformance tests
**Target Platform**: offline local library
**Project Type**: library
**Performance Goals**: deterministic reduction; no throughput claim
**Constraints**: one system, predeclared profile only, no raw restricted inputs, no admission/evaluation/conformance decision
**Scale/Scope**: one candidate row or explicit rejection per supplied capture

## Constitution Check

- Specification Authority: Pass. The implementation creates only inputs compatible with the existing Stage 1 admission vocabulary.
- Honest Conformance: Pass. Output is corpus-assembly evidence only.
- Contract-First Testing: Pass. Focused tests map to FR-001 through FR-011, especially rejection and censoring paths.
- Deterministic Core, Explicit Effects: Pass. Assembly and identity derivation are pure and offline.
- Minimal Reference Scope: Pass. No retrieval, deployment, telemetry adapter, or model logic is added.

## Project Structure

### Documentation

```text
specs/008-corpus-assembly/
├── spec.md
├── research.md
├── data-model.md
├── contracts/corpus-assembly.md
├── quickstart.md
├── plan.md
└── tasks.md
```

### Source Code

```text
isoprax/
├── admission.py
├── corpus_manifest.py
├── replay_capture.py
├── corpus_assembly.py
└── __init__.py

tests/
├── test_stage1_admission.py
└── test_corpus_assembly.py
```

**Structure Decision**: Add one corpus_assembly module beside existing deterministic evidence modules. It consumes capture records and emits existing CorpusRow-compatible data without changing admission.py.

## Complexity Tracking

No constitutional violations or extra architecture are required.
