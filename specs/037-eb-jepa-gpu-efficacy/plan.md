# Implementation Plan: EB-JEPA GPU Backend and Efficacy Gate

**Branch**: `037-eb-jepa-gpu-efficacy` | **Date**: 2026-09-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `spec.md`

## Summary

Add an optional, lazily imported PyTorch backend that adapts EB-JEPA’s
action-conditioned latent-prediction shape to Isoprax’s existing normalized event
and state-window contract. Keep the deterministic NumPy backend as the default.
Add a deterministic, predeclared efficacy evaluator that compares each family’s
held-out scores with a named baseline and returns `not_claimable` unless every
evidence gate passes. The evaluator must never pool the existing non-commensurable
Change and Operational outcomes.

## Technical Context

**Language/Version**: Python 3.10-3.14; optional PyTorch runtime selected by the user

**Primary Dependencies**: Existing NumPy/scikit-learn stack. Optional `torch` extra
for the accelerator backend; base import and tests must not require it.

**Storage**: In-memory model and evaluation report objects; existing SQLite signal
persistence remains the only persistence integration.

**Testing**: pytest with optional-dependency skips, Ruff, pre-commit, and a bounded
CPU/GPU smoke test when a usable CUDA runtime is available.

**Target Platform**: Offline Linux/Python reference implementation. CUDA is optional;
CPU execution is supported for deterministic backend tests but is not GPU evidence.

**Project Type**: Python library/reference PoC.

**Performance Goals**: Complete a bounded fixture fit and report actual device/runtime;
no throughput or speedup claim without a separate benchmark profile.

**Constraints**: Preserve unrelated dirty work, preserve the existing NumPy path and
800-row admission floor, lazy-load optional PyTorch, fail closed on missing/invalid
evidence, and do not import or vendor the external EB-JEPA repository wholesale.

**Scale/Scope**: One shared backend and the existing JIT/AIOps pair; numeric state
windows and bounded fixtures only.

## Constitution Check

| Principle | Status | Design response |
|---|---|---|
| I. Specification Authority | PASS | The feature spec defines the optional backend and evidence gate; external EB-JEPA material informs implementation shape only. |
| II. Honest Conformance | PASS | Efficacy is a scoped report status, not an automatic claim; synthetic/GPU smoke evidence is explicitly non-efficacy. |
| III. Contract-First Testing | PASS | Tests cover missing optional dependency, device failures, leakage, one-class data, non-finite metrics, and successful gate behavior. |
| IV. Deterministic Core, Explicit Effects | PASS | Inputs, seeds, identities, thresholds, and decisions are deterministic; CUDA and PyTorch are explicit effects behind a lazy boundary. |
| V. Minimal Reference Scope | PASS | The backend is a small tabular adaptation; no external corpus, provider, registry, or automatic action path is added. |

**Gate status**: PASS before research and after design.

## Project Structure

### Documentation

```text
specs/037-eb-jepa-gpu-efficacy/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/eb-jepa.md
├── quickstart.md
└── tasks.md
```

### Source Code

```text
isoprax/
├── jepa.py                    # existing deterministic NumPy backend
├── eb_jepa.py                 # optional lazy PyTorch backend and adapters
├── efficacy.py                # evidence-gated per-family efficacy report
└── __init__.py                # public exports with no eager torch import

tests/
├── test_eb_jepa.py            # optional backend contract tests
└── test_eb_jepa_efficacy.py   # fail-closed evaluator tests
```

**Structure Decision**: Keep the optional backend and its thin adapters in one module
because the repository has no model-layer package and the API surface is small. Keep
claim evaluation separate from model training so evidence policy remains deterministic
and independently testable. Use a runtime import inside the backend module so base
install behavior is unchanged.

## Complexity Tracking

No constitution violations require justification.
