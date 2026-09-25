# Tasks: Strongly Typed Python Semantic Core

**Input**: Design documents from `/specs/043-python-semantic-types/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/typed-evidence.md`

## Phase 1: Setup

- [X] T001 Add mypy to the `dev` dependency group and refresh `uv.lock` in `pyproject.toml` and `uv.lock`.
- [X] T002 Configure Python 3.10 strict checking for the declared semantic file set in `pyproject.toml`.

## Phase 2: Foundational

**Purpose**: Confirm the current Python semantic contract before changing annotations or implementation.

- [X] T003 Record current serialized decision projections and legacy constructor forms in `tests/test_commensurability.py`.

## Phase 3: User Story 1 - Construct validated semantic values (Priority: P1)

**Goal**: Keep raw inputs at parsing boundaries and store normalized, precise domain types.

**Independent Test**: Legacy supported constructors produce the same comparison results; malformed raw values fail explicitly; strict mypy accepts the normalized domain module.

- [X] T004 [US1] Add Hypothesis cases for normalized outcome construction, canonical stability, and malformed nested input in `tests/test_commensurability_properties.py`.
- [X] T005 [US1] Refactor parsing helpers and `OutcomeDefinition` storage annotations to normalized `ObservationProcess`, `Window`, and `tuple[Threshold, ...]` fields in `isoprax/commensurability.py`.
- [X] T006 [US1] Replace open commensurability level/field strings with closed literal types and validated discriminated result variants in `isoprax/commensurability.py`.
- [X] T007 [US1] Verify the strict checker passes the normalized domain and admission modules in `pyproject.toml`, `isoprax/commensurability.py`, and `isoprax/admission.py`.

## Phase 4: User Story 2 - Require typed evidence for stronger decisions (Priority: P1)

**Goal**: Make missing or mismatched declared evidence fail static checking and bind dynamic evidence to concrete definition IDs at runtime.

**Independent Test**: Valid authorization examples type-check; at least six expected-failure examples report the intended type mismatch; ID/orientation mismatch fails at runtime; Stage 0 remains Structural.

- [X] T008 [P] [US2] Add runtime tests for successful calibration qualification, missing evidence, failed calibration, and mismatched/reversed definition IDs in `tests/test_semantic_types.py`.
- [X] T009 [US2] Implement generic evidence values, validating factories, and pooled-comparison authorization in `isoprax/semantic_types.py`.
- [X] T010 [US2] Add a positive typed usage program and six named expected-failure programs for omitted or mismatched evidence in `tests/typecheck/`.
- [X] T011 [US2] Add a pytest runner that invokes mypy on positive and negative programs and checks the intended diagnostics in `tests/test_semantic_typecheck.py`.
- [X] T012 [US2] Add typed calibration and cross-family signatures while preserving report fields and Structural claim limits in `isoprax/evaluation.py` and `tests/test_evaluation.py`.

## Phase 5: User Story 3 - Enforce the typing contract in development (Priority: P1)

**Goal**: Make strict semantic checking part of local and hosted Python verification, and maintain only one semantic runtime.

**Independent Test**: `uv run mypy` passes without semantic-file suppressions; expected-failure examples are rejected; Haskell package/workflow/active documentation are absent; archived experiment evidence remains.

- [X] T013 [US3] Add strict mypy to the main Python CI test job in `.github/workflows/ci.yml`.
- [X] T014 [US3] Remove the maintained Haskell package, workflow, benchmark, differential harness, and active how-to document from `haskell/`, `.github/workflows/haskell-kernel.yml`, `scripts/benchmark_haskell_kernel.py`, `tests/`, and `docs/haskell-reference-kernel.md`.
- [X] T015 [US3] Preserve the experiment history and document the Python ownership boundary and static/runtime guarantee limits in `specs/042-haskell-semantics-kernel/assessment.md` and `docs/python-semantic-types.md`.
- [X] T016 [US3] Run the configured checker, positive/negative type examples, focused semantic tests, and Python suite; record measured checker time and results in `specs/043-python-semantic-types/converge.md`.

## Phase 6: Polish and Cross-Cutting Concerns

- [X] T017 Run `uv lock --check`, Ruff, notebook checks, and the documented cross-family demo; record only observed results in `specs/043-python-semantic-types/converge.md`.
- [X] T018 Update acceptance/task statuses and append any remaining gaps to `specs/043-python-semantic-types/converge.md`.

## Review Follow-Up

- [X] T019 Bind calibration evidence and pooled authorization to the canonical digest of the exact score/outcome samples; reject substituted samples in `isoprax/semantic_types.py` and `isoprax/evaluation.py`.
- [X] T020 Keep retained-observation mismatches bridgeable but non-poolable until outcomes are re-derived under a shared definition; update commensurability and conformance regression tests.
- [X] T021 Reject incomplete required definition fields and invalid direct `ObservationProcess`/`Window` values with focused constructor tests.
- [X] T022 Record the normative corrections and compatibility boundary in the feature research, data model, evidence contract, and convergence record.
- [X] T023 Reject unknown fields in observation-process, window, and threshold mappings; cover each dynamic boundary with regression tests.
- [X] T024 Reject non-integer and non-binary calibration outcomes before normalization and sample hashing.
- [X] T025 Keep attestations as provenance only; prevent commensurability, pooled evaluation, or shared-label pilot validation from upgrading mismatched definitions.
- [X] T026 Enforce finite, typed, nonnegative invariants in direct `Threshold` construction so validated mapping instances cannot be bypassed.

## Dependencies and Execution Order

- Setup (T001-T002) precedes all implementation work.
- Foundational contract capture (T003) precedes User Story 1.
- User Story 2 depends on the normalized outcomes and closed commensurability result from User Story 1.
- User Story 3 CI/docs cleanup depends on the type API and its examples from User Stories 1-2.
- Polish and convergence follow all stories.

## Parallel Opportunities

- T008 runtime evidence test design and the independent CI workflow edit T013 may be prepared in parallel after the contracts settle; implementation still integrates them sequentially.
- Within User Story 2, type fixtures T010 can be authored independently from runtime tests T008, but the harness T011 depends on both fixture sets and the API names from T009.
- No implementation tasks require multiple agents or parallel edits to the same semantic module.

## Implementation Strategy

1. Establish the supported legacy and result-shape baseline.
2. Normalize the core and pass strict mypy before adding evidence wrappers.
3. Add the typed evidence path with compile-time examples and runtime ID checks.
4. Integrate the checker into CI and retire Haskell's maintained source surface while retaining its research record.
5. Run focused and repository checks, measure checker duration, and converge the spec.
