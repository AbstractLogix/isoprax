# Implementation Plan: Stage 1 Per-Family Evaluation

**Branch**: `013-stage1-per-family-evaluation` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

## Summary

Define and implement deterministic, per-family Stage 1 evaluation over an
already admitted corpus using frozen splits, predeclared metrics, and explicit
calibration and uncertainty reporting. Results remain evidence-only artifacts
with a strict non-pooling and non-escalation claim boundary.

## Technical Context

**Language/Version**: Python 3.10–3.14
**Primary Dependencies**: Existing `isoprax` contracts (`admission`, `evaluation`, `commensurability`), NumPy/SciPy utilities already in project
**Storage**: N/A (in-memory deterministic reduction)
**Testing**: `pytest` + repository coverage gates
**Target Platform**: Offline library execution in CI/local
**Project Type**: Single-package reference library
**Performance Goals**: Deterministic output identity and ordering for equivalent inputs
**Constraints**: No cross-family pooling, no post-hoc thresholding, no conformance upgrade claims, fail-closed on non-admission/missing evidence
**Scale/Scope**: One admitted corpus + one family + one outcome definition per evaluation run

## Constitution Check

| Principle | Design response | Result |
| --- | --- | --- |
| Specification Authority | Evaluation consumes admission outputs and preserves explicit boundaries from the feature spec. | Pass |
| Honest Conformance | Report class stays below Semantic/Full and never presents efficacy claims. | Pass |
| Contract-First Testing | Determinism, split isolation, missing evidence, and rejection paths are covered with focused tests. | Pass |
| Deterministic Core, Explicit Effects | Canonical serialization/hashing and split filtering are pure and offline. | Pass |
| Minimal Reference Scope | Adds one small evaluation module + tests; no adapter or platform expansion. | Pass |

Post-design re-check: Pass.

## Project Structure

### Documentation

```text
specs/013-stage1-per-family-evaluation/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── per-family-evaluation.md
├── tasks.md
├── converge.md
└── checklists/
    └── requirements.md
```

### Source impact

```text
isoprax/
├── evaluation.py                    # existing metric/calibration utilities
├── admission.py                     # existing admissibility gate contract
├── (new) per_family_evaluation.py   # deterministic per-family Stage 1 reducer
└── __init__.py                      # public exports

tests/
└── test_per_family_evaluation.py
```

**Structure Decision**: Keep per-family evaluation as a narrow library seam
that composes existing admission + calibration primitives while preserving
explicit claim limits.

## Complexity Tracking

No constitution exceptions required.
