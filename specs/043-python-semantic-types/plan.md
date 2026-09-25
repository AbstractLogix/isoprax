# Implementation Plan: Strongly Typed Python Semantic Core

**Branch**: `codex/043-python-semantic-types` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/043-python-semantic-types/spec.md`

## Summary

Make Python's deterministic semantic core the only maintained implementation. Normalize untrusted outcome inputs into domain-only fields, expose a typed evidence authorization path for declared outcome families, and enforce a strict mypy check on the semantic core and its calibration/reporting decisions. Keep runtime ID checks authoritative for data-derived definitions. Retire the Haskell package and active CI/docs while preserving its completed experiment record under `specs/042-haskell-semantics-kernel/`.

## Technical Context

**Language/Version**: Python 3.10 through 3.14; use syntax available on Python 3.10.

**Primary Dependencies**: Add mypy to the `dev` dependency group only. Reuse dataclasses, `typing`, NumPy, Hypothesis, and pytest already in the project.

**Storage**: No change. Existing JSON and persisted Outcome Definition shapes remain compatible.

**Testing**: Focused commensurability and evaluation tests, Hypothesis invariants, positive and expected-failure mypy examples, then the existing Python suite and documented demo.

**Target Platform**: Existing Linux and Windows development/CI platforms, Python 3.10, 3.12, and 3.14 test matrix.

**Project Type**: Python reference library with offline research/evaluation tooling.

**Performance Goals**: No runtime dependency or material overhead from typing. Static check completes under two minutes on hosted Linux.

**Constraints**: Preserve current decisions, reason codes, and serialized fields. Keep arbitrary external input at validated runtime boundaries. The Python checker scope must be explicit and free of error suppressions. Generic evidence tags can protect statically declared outcome families; dynamic IDs still require runtime binding checks. No migration of data processing, ML/JEPA, notebooks, or numerical workflows.

**Scale/Scope**: `isoprax/commensurability.py`, `isoprax/admission.py`, a small `isoprax/semantic_types.py` evidence layer, selected signatures in `isoprax/evaluation.py`, their focused tests, and removal of maintained Haskell sources/workflow/benchmark/docs.

## Constitution Check

| Principle | Gate | Result |
|---|---|---|
| Specification Authority | Preserve normative decisions and reason codes; malformed input fails explicitly. | Pass |
| Honest Conformance | Typed evidence cannot upgrade Stage 0 Structural results. | Pass |
| Contract-First Testing | Cover accepted and rejected evidence flows, malformed input, and decision invariants. | Pass |
| Deterministic Core, Explicit Effects | Keep parsing and decisions pure; checker and property tests use no network or state. | Pass |
| Minimal Reference Scope | Type the commensurability/calibration seam; leave ML, corpus pipelines, and orchestration in Python as today. | Pass |

## Phase 0: Research Decisions

See [research.md](research.md). The selected checker is mypy strict mode, configured only for the stated semantic files. Python's generic phantom tags express consistency between declared evidence types; explicit runtime ID checks remain mandatory because static types cannot prove equality of values loaded from JSON or a database.

## Phase 1: Design

See [data-model.md](data-model.md) and [contracts/typed-evidence.md](contracts/typed-evidence.md). `OutcomeDefinition` stores normalized domain fields after construction. Typed authorization values are created only by validating factories and carry the runtime IDs they bind. Decision levels use closed literal types and preserve current output values.

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

**Structure Decision**: Extend the existing Python semantic modules and add one small typed evidence module. Do not create a second runtime, service, or broad typing retrofit. Remove the old Haskell CI workflow and sources; keep the historical experiment specification, benchmark results, and decision record.

## Complexity Tracking

No constitution gate violations or additional architectural projects are introduced.
