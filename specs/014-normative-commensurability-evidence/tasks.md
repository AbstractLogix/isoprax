---
description: "Implementation tasks for normative authority and commensurability evidence"
---

# Tasks: Normative Authority and Commensurability Evidence

**Input**: Design documents from `specs/014-normative-commensurability-evidence/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

## Phase 1: Setup

- [X] T001 Vendor the exact authoritative Isoprax v0.3 `SPEC.md` into `docs/isoprax-v0.3-poc.md` and record source/provenance in `docs/isoprax-v0.3-poc-provenance.md`
- [X] T002 [P] Add Feature 014 test module files under `tests/` with focused names for citations, commensurability, evaluation, ForecastStrategy, and pooling harm
- [X] T003 [P] Add the Feature 014 public exports to `isoprax/__init__.py` only after the corresponding contracts exist

## Phase 2: Foundational

- [X] T004 Implement citation extraction and numbered-anchor resolution in `isoprax/normative.py`, including source locations and full appendix/subsection references
- [X] T005 [P] Add citation-resolution failure and success fixtures in `tests/test_normative_citations.py`
- [X] T006 [P] Define structured window, threshold, observation-process, and attestation value objects in `isoprax/commensurability.py`
- [X] T007 [P] Add deterministic serialization and backward-compatible `OutcomeDefinition` conversion tests in `tests/test_commensurability.py`
- [X] T008 Run the citation and structured-definition tests and confirm the foundational contracts fail closed before story implementation

## Phase 3: User Story 1 - Verify the normative authority (Priority: P1)

**Goal**: Every normative citation in `isoprax/` resolves to the vendored v0.3 authority.

**Independent Test**: `uv run pytest tests/test_normative_citations.py -q`

- [X] T009 [US1] Wire the citation scan to walk only implementation source files and report unresolved source path, line, and full reference in `isoprax/normative.py`
- [X] T010 [US1] Add tests for 5.2, 5.6.3, 8.2, D.3, Appendix D, malformed references, and generated-file exclusion in `tests/test_normative_citations.py`
- [X] T011 [US1] Update README authority/provenance wording to point to the vendored document and preserve the external-source provenance in `README.md`

## Phase 4: User Story 2 - Assess definitions without circular reasoning (Priority: P1)

**Goal**: Definition comparisons are structured, graded, deterministic, and provenance-aware.

**Independent Test**: `uv run pytest tests/test_commensurability.py -q`

- [X] T012 [US2] Replace free-form comparison fields with typed canonical values while preserving existing public construction compatibility in `isoprax/commensurability.py`
- [X] T013 [US2] Implement direct, attested, bridgeable, and irreducible assessment levels with field-level reasons and pooling policy in `isoprax/commensurability.py`
- [X] T014 [US2] Implement attestation and bridge evidence validation, including named provenance and required retained-observation evidence in `isoprax/commensurability.py`
- [X] T015 [US2] Update registry and SQLiteKB definition round trips for structured definitions in `isoprax/commensurability.py` and `isoprax/kb.py`
- [X] T016 [US2] Add tests for wording/order equivalence, recoverable window/threshold mismatches, irreducible event/process mismatches, invalid attestations, and round trips in `tests/test_commensurability.py`

## Phase 5: User Story 3 - Demonstrate pooling harm (Priority: P1)

**Goal**: A deterministic same-event seven-day versus ninety-day fixture demonstrates acceptable pooled ECE can mask degraded top-k selection.

**Independent Test**: `uv run pytest tests/test_pooling_harm.py -q`

- [X] T017 [US3] Add deterministic pooling-harm fixture generation and per-family/pooled ECE and top-k metrics in `isoprax/evidence.py`
- [X] T018 [US3] Add tests asserting both family ECE values are below 0.05, pooled ECE is apparently acceptable, and pooled top-k degradation is positive in `tests/test_pooling_harm.py`
- [X] T019 [US3] Update `CrossFamilyReport` and `examples/demo_cross_family.py` to report descriptive pooled masking evidence without permitting non-commensurable pooling

## Phase 6: User Story 4 - Distinguish calibration from useful prediction (Priority: P1)

**Goal**: Calibration qualification withholds the calibrated declaration for constant or otherwise degenerate predictors.

**Independent Test**: `uv run pytest tests/test_evaluation.py -q`

- [X] T020 [US4] Add discrimination diagnostics and qualification fields, including ROC AUC, score variation, class counts, and explicit unavailable states in `isoprax/evaluation.py`
- [X] T021 [US4] Require non-degenerate discrimination in `check_calibration_conformance` while preserving existing sample/ECE gates in `isoprax/evaluation.py`
- [X] T022 [US4] Add tests for constant base-rate, informative, one-class, insufficient, and isotonic-collapse predictors in `tests/test_evaluation.py`
- [X] T023 [US4] Update calibration declarations and demo output to distinguish calibration from discrimination in `examples/demo_cross_family.py`

## Phase 7: User Story 5 - Exercise ForecastStrategy end to end (Priority: P2)

**Goal**: A concrete ForecastStrategy produces a score-free ForecastSignal and round-trips through SQLiteKB.

**Independent Test**: `uv run pytest tests/test_forecast_strategy.py -q`

- [X] T024 [US5] Implement a deterministic history-based ForecastStrategy and ForecastSignal provenance in `isoprax/baseline_strategies.py`
- [X] T025 [US5] Extend SQLiteKB signal storage/retrieval so ForecastSignal fields round-trip without assuming a probability score in `isoprax/kb.py`
- [X] T026 [US5] Add end-to-end event, definition, ForecastSignal, and retrieval tests including score rejection in `tests/test_forecast_strategy.py`
- [X] T027 [US5] Update the demo strategy count and Full Conformance caveat after the third strategy is exercised in `examples/demo_cross_family.py`

## Phase 8: User Story 6 - Public label evidence anchor (Priority: P3)

**Goal**: Public SZZ-style label evidence is manifest-driven and fail-closed.

**Independent Test**: `uv run pytest tests/test_public_label_evidence.py -q`

- [X] T028 [US6] Define a license-aware public label evidence manifest and blocked/inconclusive status reducer in `isoprax/public_label_evidence.py`
- [X] T029 [US6] Add supplied-fixture tests for valid provenance, label disagreement, unavailable sources, license gaps, and changed source identities in `tests/test_public_label_evidence.py`
- [X] T030 [US6] Add the public evidence manifest template and claim-boundary documentation under `examples/public-label-evidence/`

## Phase 9: Polish and validation

- [X] T031 [P] Export new public contracts from `isoprax/__init__.py` and update `README.md` usage/claim-boundary documentation
- [X] T032 [P] Run Ruff formatting/checks and fix only Feature 014 findings in changed Python files
- [X] T033 Run focused Feature 014 tests and the existing conformance suite with `uv run pytest`
- [X] T034 Run the documented demo, `git diff --check`, and repository coverage checks; record evidence and remaining blocked public-data state in `specs/014-normative-commensurability-evidence/converge.md`

## Dependencies and execution order

- T001–T008 are foundational; T001 must precede T004/T009.
- US1 and US2 depend on T004/T006; US3 depends on structured definitions; US4 is independent after the foundational phase; US5 depends on the existing KB contract; US6 is independent and supplied-fixture-only.
- T031–T034 follow all desired stories. T032 and T033 can run in parallel after implementation, but T034 consumes their results.

## MVP scope

T001–T016 plus T020–T023: vendored authority, citation gate, graded structured commensurability, and non-degenerate calibration. The pooling-harm fixture is the next required evidence slice; public-label material remains fail-closed and may be blocked.
