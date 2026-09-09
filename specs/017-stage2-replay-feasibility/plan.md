# Implementation Plan: Stage 2 Deterministic Replay Feasibility

**Branch**: `codex/017-stage2-replay-feasibility` | **Date**: 2026-09-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/017-stage2-replay-feasibility/spec.md`

## Summary

Add a deterministic feasibility reducer for a bounded Stage 2 replay pilot. The
implementation composes existing predeclaration, structured commensurability,
hermetic execution, replay capture, and corpus-assembly contracts; it retains
every selected revision in a terminal record and produces a claim-bounded
`feasible`, `inconclusive`, or `blocked` report. No runner, cloud adapter, full
corpus, pooled metric, or Semantic claim is added.

## Technical Context

**Language/Version**: Python 3.10–3.14

**Primary Dependencies**: Existing standard library, NumPy/SciPy/scikit-learn only where existing report contracts require them, and Isoprax replay modules

**Storage**: In-memory immutable dataclasses plus canonical JSON evidence manifests; no database

**Testing**: Focused pytest conformance tests, Ruff, then full pytest/coverage

**Target Platform**: Offline Python reference implementation on Linux/WSL

**Project Type**: Deterministic Python library and evidence-reporting slice

**Performance Goals**: Linear reduction over pilot terminal records; deterministic report generation without network or raw-payload loading

**Constraints**: Fail closed on invalid provenance, missing terminal outcomes, private/privileged evidence, definition mismatch, and mutable lane metadata; preserve all censoring

**Scale/Scope**: One public system/service, one bounded pilot sample, one frozen lane definition, and repeated execution only when explicitly declared

## Constitution Check

| Principle | Design response | Result |
| --- | --- | --- |
| Specification Authority | Reuses the Stage 2 feasibility boundary and existing normative replay/capture contracts. | Pass |
| Honest Conformance | Emits feasibility status only and withholds Semantic, pooled, and full-corpus claims. | Pass |
| Contract-First Testing | Adds focused tests for every status, denominator, provenance, commensurability, and determinism rule. | Pass |
| Deterministic Core | Uses immutable inputs, canonical hashing, injected effects, and offline validation. | Pass |
| Minimal Reference Scope | Adds one reporting module and no concrete infrastructure adapter or external service. | Pass |

**Post-design gate**: Pass. The design stays within one package, adds no
network dependency or infrastructure decision, and does not weaken existing
Structural/Semantic claim boundaries.

## Project Structure

### Documentation (this feature)

```text
specs/017-stage2-replay-feasibility/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/requirements.md
└── tasks.md                 # created by speckit-tasks
```

### Source Code (repository root)

```text
isoprax/
├── stage2_feasibility.py       # pilot profile, terminal/repeatability records, report reducer
├── replay_capture.py           # existing lane/effect boundary
├── commensurability.py         # existing structured definition comparison
├── corpus_assembly.py          # existing capture-to-row evidence reducer
└── predeclaration.py           # existing ordering/provenance contracts
tests/
└── test_stage2_feasibility.py  # focused contract and rejection-path tests
```

**Structure Decision**: Keep the feature in the existing single Python package
and test layout. The new module is a pure reducer; infrastructure remains an
injected caller concern. No CLI or external contract is needed for this slice.

## Design

1. Define an immutable `ReplayPilotProfile` that canonicalizes selected
   revisions, release scope, predeclaration ordering evidence, prediction-time
   fields, thresholds, and both structured outcome definitions.
2. Validate direct/attested/bridgeable/irreducible commensurability using
   `check_commensurable`; permit a shared-label feasibility gate only for direct
   or valid attested equivalence. Record bridgeable mismatches as a non-semantic
   condition rather than silently pooling them.
3. Normalize existing `ReplayCaptureRecord` values into one terminal record per
   selected commit. Preserve censoring and blocked-before-compilation reasons,
   and reject duplicates, missing commits, mutable lane metadata, or unsafe
   evidence scope.
4. Compare explicitly supplied repeated runs by lane identity and canonical
   terminal evidence. Preserve field-level disagreements and produce a
   repeatability result instead of averaging runs.
5. Build a canonical `FeasibilityReport` with counts, denominated rates,
   temporal coverage, elapsed/resource metadata, release gates, extrapolation
   assumptions, and a single status. Hash only public canonical metadata.
6. Export the new public types from `isoprax.__init__`, add focused tests for
   happy paths and every fail-closed requirement, then run the documented
   focused and full checks.

## Complexity Tracking

No constitution violations identified. The plan deliberately avoids a concrete
runner, persistent store, network adapter, or new external contract.
