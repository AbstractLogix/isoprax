# Implementation Plan: Stage 1 Evidence Reporting

**Branch**: `009-evidence-reporting` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

## Summary

Add one deterministic, offline reporting module that reduces Feature 008 corpus
assembly, Feature 002 admission, and Feature 007 replay-capture records to a
safe publication summary. It validates that the records describe the same
frozen profile and accepted rows, surfaces missing evidence as unavailable,
and fixes the claim boundary at admission evidence only.

## Technical Context

**Language/Version**: Python 3.10–3.14
**Primary Dependencies**: Python standard library; existing Isoprax dataclasses
**Storage**: N/A; callers own persistence/publication
**Testing**: pytest with repository coverage gate
**Target Platform**: Offline Python library
**Project Type**: Single-package reference library
**Performance Goals**: Deterministic reduction of one in-memory corpus without network I/O
**Constraints**: No raw prediction/deployment/observation payloads; no conformance upgrade; deterministic canonical output; fail closed on contradictory lineage or private/privileged provenance
**Scale/Scope**: One assembled single-system corpus and its bounded replay-capture evidence per report

## Constitution Check

| Principle | Design response | Result |
|---|---|---|
| Specification Authority | The reporter only reduces existing Stage 1 contract results and preserves their explicit claim limits. | Pass |
| Honest Conformance | A fixed report claim boundary explicitly withholds Semantic/Full, efficacy, and pooling claims. | Pass |
| Contract-First Testing | Focused tests cover determinism, safe reduction, unavailable evidence, status, and fail-closed rejection paths. | Pass |
| Deterministic Core, Explicit Effects | Canonical serialization and sorting are pure; no I/O or network access occurs. | Pass |
| Minimal Reference Scope | One library module and test file; no publisher, adapter, persistence, or remediation abstraction. | Pass |

Post-design result: Pass. No constitution exception or complexity tracking is required.

## Project Structure

```text
isoprax/
├── admission.py             # existing authoritative gate evaluation
├── corpus_assembly.py       # existing accepted-row/profile report
├── replay_capture.py        # existing safe capture evidence
├── evidence_reporting.py    # new deterministic public report reduction
└── __init__.py              # public exports

tests/
└── test_evidence_reporting.py

specs/009-evidence-reporting/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/evidence-reporting.md
```

**Structure Decision**: Keep the report reducer adjacent to its three source
contracts. It has no external interface or persistence requirement.

## Complexity Tracking

No violations.
