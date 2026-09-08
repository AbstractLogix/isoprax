---

description: "Implementation tasks for Stage 2 deterministic replay feasibility"
---

# Tasks: Stage 2 Deterministic Replay Feasibility

**Input**: Design documents from `/specs/017-stage2-replay-feasibility/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, and `quickstart.md`

**Tests**: Included because the specification and constitution require focused conformance and rejection-path tests.

## Phase 1: Setup

**Purpose**: Confirm the existing package/test seams and reserve the new module without adding infrastructure.

- [X] T001 Confirm existing replay, commensurability, predeclaration, and evidence-reporting exports in `isoprax/__init__.py`
- [X] T002 [P] Add the Stage 2 module/test paths to the implementation notes in `specs/017-stage2-replay-feasibility/plan.md`

## Phase 2: Foundational Contracts

**Purpose**: Establish canonical validation and identity helpers that all user stories consume.

- [X] T003 Define immutable `ReplayPilotProfile`, status literals, claim boundary, and canonical profile identity in `isoprax/stage2_feasibility.py`
- [X] T004 [P] Define `ReplayTerminalRecord`, `RepeatabilityCheck`, gate summaries, and `FeasibilityReport` data entities in `isoprax/stage2_feasibility.py`
- [X] T005 [P] Add constructor and canonicalization rejection tests for empty samples, duplicate commits, malformed metadata, and invalid status values in `tests/test_stage2_feasibility.py`
- [X] T006 Implement predeclaration ordering, candidate/system boundary, frozen lane metadata, and prediction-time validation in `isoprax/stage2_feasibility.py`
- [X] T007 Add public exports for the Stage 2 entities and report builder in `isoprax/__init__.py`

**Checkpoint**: Foundation exposes deterministic immutable inputs and rejects invalid pilot profiles before any report is built.

## Phase 3: User Story 1 - Freeze a Replay Pilot (Priority: P1) 🎯 MVP

**Goal**: Accept only an auditable, predeclared pilot with structured shared outcome semantics.

**Independent Test**: Build a valid profile from fixed definitions and verify deterministic identity; reject missing anchor/ancestry, mutable lane metadata, and irreducible definitions.

### Tests for User Story 1

- [X] T008 [P] [US1] Test direct, attested, bridgeable, and irreducible outcome-definition handling in `tests/test_stage2_feasibility.py`
- [X] T009 [P] [US1] Test predeclaration hash/anchor ancestry and frozen profile mismatch rejection in `tests/test_stage2_feasibility.py`

### Implementation for User Story 1

- [X] T010 [US1] Implement structured commensurability gate and preserved attestation metadata in `isoprax/stage2_feasibility.py`
- [X] T011 [US1] Implement profile-to-lane validation for system/service, workload, horizon, thresholds, schema, and evidence scope in `isoprax/stage2_feasibility.py`
- [X] T012 [US1] Implement deterministic profile serialization and identity validation in `isoprax/stage2_feasibility.py`

**Checkpoint**: A valid pilot can be frozen and independently revalidated before replay records are accepted.

## Phase 4: User Story 2 - Run a Bounded Replay Lane (Priority: P1)

**Goal**: Normalize existing capture evidence into exactly one terminal record per selected revision while preserving censoring and blocking.

**Independent Test**: Supply complete, censored, and blocked captures and verify terminal status, reasons, lineage, and denominator preservation.

### Tests for User Story 2

- [X] T013 [P] [US2] Test one-terminal-record-per-commit, duplicate detection, missing commit detection, and lane identity checks in `tests/test_stage2_feasibility.py`
- [X] T014 [P] [US2] Test complete shared observation labels, censored captures, blocked-before-compilation records, and private/privileged evidence rejection in `tests/test_stage2_feasibility.py`

### Implementation for User Story 2

- [X] T015 [US2] Implement capture normalization into `ReplayTerminalRecord` with explicit stage and censor reasons in `isoprax/stage2_feasibility.py`
- [X] T016 [US2] Implement terminal-record lineage, artifact-scope, and prediction-time checks against existing `ReplayCaptureRecord` values in `isoprax/stage2_feasibility.py`
- [X] T017 [US2] Implement denominator and temporal-coverage aggregation for selected, terminal, complete, positive, negative, censored, blocked, and withheld records in `isoprax/stage2_feasibility.py`

**Checkpoint**: A bounded pilot reports every selected revision exactly once without converting replay failure into a negative outcome.

## Phase 5: User Story 3 - Measure Feasibility and Repeatability (Priority: P1)

**Goal**: Produce a deterministic feasibility status with throughput, yield, release, and repeatability gates.

**Independent Test**: Build reports for feasible, inconclusive, and blocked pilots and verify status reasons, counts, rates, repeat-run discrepancies, and claim withholding.

### Tests for User Story 3

- [X] T018 [P] [US3] Test feasible, inconclusive, and blocked status selection from declared gates in `tests/test_stage2_feasibility.py`
- [X] T019 [P] [US3] Test repeatability pass/fail/inconclusive comparisons and deterministic report identity in `tests/test_stage2_feasibility.py`
- [X] T020 [P] [US3] Test throughput/resource metadata, extrapolation assumptions, and no-survivor-only rates in `tests/test_stage2_feasibility.py`

### Implementation for User Story 3

- [X] T021 [US3] Implement repeatability comparison preserving terminal, label, artifact, and evidence discrepancies in `isoprax/stage2_feasibility.py`
- [X] T022 [US3] Implement denominated rates, throughput/resource summaries, extrapolation metadata, and release-readiness gates in `isoprax/stage2_feasibility.py`
- [X] T023 [US3] Implement `build_stage2_feasibility_report` with exclusive `feasible`/`inconclusive`/`blocked` status and explicit claim boundary in `isoprax/stage2_feasibility.py`

**Checkpoint**: The report is independently reproducible and does not emit Semantic, pooled-performance, or full-corpus claims.

## Phase 6: User Story 4 - Publish a Bounded Evidence Package (Priority: P2)

**Goal**: Make the feasibility report independently verifiable from public canonical artifacts.

**Independent Test**: Serialize and revalidate a report without raw payloads or private telemetry, reproducing identity, counts, gates, and claim boundary.

### Tests for User Story 4

- [X] T024 [P] [US4] Test canonical public serialization, hash-linked manifest validation, and raw-payload exclusion in `tests/test_stage2_feasibility.py`
- [X] T025 [P] [US4] Test release blocking for private/privileged evidence and missing artifact lineage in `tests/test_stage2_feasibility.py`

### Implementation for User Story 4

- [X] T026 [US4] Implement report serialization and independent `validate_stage2_feasibility_report` reconstruction in `isoprax/stage2_feasibility.py`
- [X] T027 [US4] Add Stage 2 quickstart/reporting references to `README.md` without presenting feasibility as Semantic validation

**Checkpoint**: A reviewer can validate the report from released metadata and see exactly what remains unproven.

## Phase 7: Polish and Cross-Cutting Validation

**Purpose**: Verify the whole feature against the repository gates and update feature artifacts.

- [X] T028 [P] Run focused Stage 2 tests and Ruff checks from `specs/017-stage2-replay-feasibility/quickstart.md`
- [X] T029 Run full `uv run pytest` with the repository coverage gate and record any per-module coverage issue in `specs/017-stage2-replay-feasibility/quickstart.md`
- [X] T030 [P] Run `uv run ruff check .` and resolve only Stage 2 findings in `isoprax/stage2_feasibility.py`, `isoprax/__init__.py`, and `tests/test_stage2_feasibility.py`
- [X] T031 Run the convergence check and append any remaining implementation tasks to this file only if the spec is not satisfied

## Phase 8: Convergence

**Purpose**: Close partial implementation gaps identified by the spec-to-code convergence review.

- [X] T032 [US2] Persist explicit Change-family and Operational-family labels and shared-observation lineage on every normalized complete terminal record per FR-008 in `isoprax/stage2_feasibility.py` (partial)
- [X] T033 [US2] Accept and validate prediction-time field evidence against allowed/forbidden declarations and score-time boundaries per FR-009 in `isoprax/stage2_feasibility.py` and `tests/test_stage2_feasibility.py` (partial)
- [X] T034 [US4] Validate non-empty qualification, execution, deployment, and artifact hash lineage before reporting release readiness per FR-013 in `isoprax/stage2_feasibility.py` and `tests/test_stage2_feasibility.py` (partial)
- [X] T035 [US3] Derive temporal coverage from normalized lane timestamps and expose it in the report instead of relying only on caller-supplied metadata per FR-010 and SC-004 in `isoprax/stage2_feasibility.py` and `tests/test_stage2_feasibility.py` (partial)

## Phase 9: Injected Pilot Integration

**Purpose**: Exercise the complete offline pipeline before selecting a real public-project adapter.

- [X] T036 [US2] Add an injected end-to-end pilot test covering build qualification, hermetic execution, replay capture, terminal normalization, and feasibility-report validation in `tests/test_stage2_pilot_integration.py`

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 has no dependencies.
- Phase 2 depends on Phase 1 and blocks all user stories.
- User Stories 1 and 2 are sequential because capture validation depends on a frozen profile; both are required before User Story 3.
- User Story 4 depends on User Story 3's report shape.
- Phase 7 depends on all desired user stories.

### User Story Dependencies

- **US1**: Starts after Phase 2; establishes the immutable profile and semantic gate.
- **US2**: Depends on US1; consumes the frozen profile and existing capture records.
- **US3**: Depends on US2; aggregates terminal records and repeat runs.
- **US4**: Depends on US3; serializes and independently validates the report.

### Parallel Opportunities

- T004 and T005 can run in parallel with T003 after the module seam is agreed.
- T008/T009, T013/T014, T018/T020, and T024/T025 are parallel test-writing tasks within their story.
- T028 and T030 can run in parallel after implementation.

## Implementation Strategy

1. Complete the profile and commensurability MVP (US1), then validate it.
2. Add capture normalization and denominator preservation (US2).
3. Add feasibility status, repeatability, and extrapolation reporting (US3).
4. Add public serialization and README guidance (US4).
5. Run focused checks, full CI-equivalent tests, and convergence.

The finished feature is a feasibility evidence gate. A subsequent feature is
required for full corpus acquisition and Semantic evaluation.
