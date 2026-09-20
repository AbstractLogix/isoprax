# Implementation Plan: JEPA Unified Predictor

**Branch**: `036-jepa-unified-predictor` | **Date**: 2026-09-20 | **Spec**: [spec.md](spec.md)

## Summary

Add a deterministic, offline action-conditioned latent predictor to the Isoprax PoC.
It encodes normalized change events and fixed operational metric windows, fits a
representation-space predictor without outcome labels, and exposes two thin readout
adapters: a change-family risk signal from the change embedding and an
operational-family anomaly signal from latent prediction error. Existing calibration,
admission, evaluation, persistence, and the existing 800-row test-row floor remain
unchanged.

The reference backend is intentionally a small NumPy implementation. It proves the
strategy boundary and shared-representation provenance in the current dependency
set; it does not pretend to be the recommended GPU research backend or provide
empirical efficacy evidence.

## Technical Context

**Language/Version**: Python 3.10-3.14

**Primary Dependencies**: Existing NumPy dependency; existing `Calibrator`, Signals,
events, and Outcome Definition contracts. No new dependency.

**Storage**: In-memory model objects; signals remain persistable through the existing
SQLite knowledge base. No model registry or network storage.

**Testing**: pytest, repository coverage gate, Ruff, and pre-commit.

**Target Platform**: Offline Linux/Python reference implementation; no GPU required.

**Project Type**: Python library/reference PoC.

**Performance Goals**: Deterministic fitting and inference for focused PoC-sized
windows; no production throughput claim.

**Constraints**: No network access, no raw restricted data in reports, fail closed on
malformed inputs, preserve existing strategy and admission contracts, and report
Structural conformance only unless validated evidence satisfies the explicit gate.

**Scale/Scope**: One repository and one JIT/AIOps family pair, with fixed-dimensional
numeric state windows and bounded deterministic test fixtures.

## Constitution Check

| Principle | Status | Design response |
|---|---|---|
| Specification Authority | PASS | The attached feature spec is translated into `spec.md`; existing normative contracts remain authoritative. |
| Honest Conformance | PASS | Default report is Structural; calibration and shared code cannot produce a Semantic claim. |
| Contract-First Testing | PASS | Focused tests cover training, signal, persistence, calibration, and rejection paths. |
| Deterministic Core, Explicit Effects | PASS | NumPy fitting is deterministic and offline; adapters are thin and signals use existing contracts. |
| Minimal Reference Scope | PASS | A dependency-light reference backend is added only because this feature explicitly requires JEPA/profile work; no external replay or provider code is added. |

## Project Structure

```text
isoprax/
├── jepa.py                 # encoders, predictor, readouts, conformance evidence
├── __init__.py             # public exports
├── events.py               # existing normalized input types
├── signals.py              # existing output contracts
└── strategies.py           # existing abstract strategy contracts

tests/
└── test_jepa.py            # feature and contract conformance tests

specs/036-jepa-unified-predictor/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/jepa-strategy.md
├── quickstart.md
└── tasks.md
```

**Structure Decision**: Keep the feature in one `isoprax/jepa.py` module because the
reference scope is intentionally small and the existing package has no model-layer
subtree. Split only the stable public contract into dataclasses and adapters; do not
introduce a registry, service, or backend framework.

## Complexity Tracking

No constitution violations require justification.
