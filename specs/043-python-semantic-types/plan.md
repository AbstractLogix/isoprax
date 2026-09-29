# Implementation Plan: Strongly Typed Python Semantic Core

**Branch**: `codex/044-ci-semantics-oracle` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/043-python-semantic-types/spec.md`

## Summary

Keep Python as the sole runtime implementation of Isoprax semantic decisions. Normalize untrusted outcome inputs into domain-only fields, expose a typed evidence authorization path for declared outcome families, and enforce a strict mypy check on the semantic core and its calibration/reporting decisions. Bind runtime evidence to concrete IDs, normalized definition semantics, exact samples, and a shared calibration policy. Retain a small Haskell oracle in CI for those semantic contracts, with no Python runtime dependency.

## Technical Context

**Language/Version**: Python 3.10 through 3.14; use syntax available on Python 3.10.

**Primary Dependencies**: Add mypy to the `dev` dependency group only. Reuse dataclasses, `typing`, NumPy, Hypothesis, and pytest already in the Python project. Pin GHC/Cabal and the small Haskell oracle's package plan in its own CI-only project.

**Storage**: No change. Existing JSON and persisted Outcome Definition shapes remain compatible.

**Testing**: Focused commensurability and evaluation tests, Hypothesis invariants, positive and expected-failure mypy examples, Python/Haskell shared fixtures, Haskell QuickCheck properties and compile-fail examples, then the existing Python suite and documented demo.

**Target Platform**: Existing Linux and Windows development/CI platforms, Python 3.10, 3.12, and 3.14 test matrix.

**Project Type**: Python reference library with offline research/evaluation tooling.

**Performance Goals**: No runtime dependency or material overhead from typing. Static check completes under two minutes on hosted Linux.

**Constraints**: Preserve current decisions, reason codes, and serialized fields. Keep arbitrary external input at validated runtime boundaries. The Python checker scope must be explicit and free of error suppressions. Generic evidence tags can protect statically declared outcome families; dynamic evidence binds definition ID plus normalized semantic-content digest. Both calibrations must carry the same validated policy, and pooled ECE must use that policy's bin count. The report facade retains pooled ECE as an explicitly diagnostic output. Haskell is a CI-only oracle for the semantic proof boundary and is never imported, spawned, or required by Python runtime code. No migration of data processing, ML/JEPA, notebooks, or numerical workflows.

**Scale/Scope**: `isoprax/commensurability.py`, `isoprax/admission.py`, a small `isoprax/semantic_types.py` evidence layer, selected signatures in `isoprax/evaluation.py`, focused Python tests, and a compact Haskell oracle under `haskell/semantic-oracle/` with shared fixtures and a semantic-path CI workflow. Admission, ML, benchmark, and runtime bridge behavior are outside the Haskell oracle.

## Constitution Check

| Principle | Gate | Result |
|---|---|---|
| Specification Authority | Preserve normative decisions and reason codes; malformed input fails explicitly. | Pass |
| Honest Conformance | Typed evidence cannot upgrade Stage 0 Structural results. | Pass |
| Contract-First Testing | Cover accepted and rejected evidence flows, malformed input, and decision invariants. | Pass |
| Deterministic Core, Explicit Effects | Keep parsing and decisions pure; checker and property tests use no network or state. | Pass |
| Minimal Reference Scope | Type the commensurability/calibration seam; leave ML, corpus pipelines, and orchestration in Python, and keep Haskell CI-only. | Pass |

## Phase 0: Research Decisions

See [research.md](research.md). The selected checker is mypy strict mode, configured only for the stated semantic files. Python's generic phantom tags express consistency between declared evidence types; explicit runtime ID checks remain mandatory because static types cannot prove equality of values loaded from JSON or a database.

## Phase 1: Design

See [data-model.md](data-model.md) and [contracts/typed-evidence.md](contracts/typed-evidence.md). `OutcomeDefinition` stores normalized domain fields after construction. Typed authorization values are created only by validating factories and carry the runtime IDs, normalized definition digests, exact sample digests, and shared `CalibrationPolicy` they bind. Direct `ObservationProcess` parameters validate and sort inside `__post_init__`. Decision levels use closed literal types and preserve current output values. The report facade remains an explicitly diagnostic path and cannot issue typed authorization.

## Project Structure

### Documentation

```text
specs/043-python-semantic-types/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/typed-evidence.md
└── tasks.md
```

### Source Code

```text
isoprax/
├── commensurability.py       # normalized values and closed decision results
├── semantic_types.py         # generic evidence tokens and checked authorization
├── evaluation.py             # typed calibration and cross-family boundary signatures
└── admission.py              # closed split, outcome, and gate identifiers

tests/
├── test_commensurability.py
├── test_semantic_types.py
├── test_evaluation.py
└── typecheck/                 # positive and expected-failure mypy programs

docs/
└── python-semantic-types.md   # ownership boundary and static/runtime guarantee limits
```

**Structure Decision**: Extend the existing Python semantic modules and add one small typed evidence module. Do not create a second runtime, service, or broad typing retrofit. Keep a separate, compact Haskell oracle that checks the proof boundary through shared fixtures and generated tests only when semantic contract paths change.

## Complexity Tracking

No constitution gate violations or additional architectural projects are introduced.
