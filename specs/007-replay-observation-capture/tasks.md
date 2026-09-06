# Tasks: Replay Observation Capture

**Input**: Design documents from `/specs/007-replay-observation-capture/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/replay-capture-backend.md, quickstart.md

**Tests**: Focused pytest conformance tests are required by the specification and Constitution III.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

**Purpose**: Establish the feature test boundary without adding infrastructure.

- [X] T001 Verify existing Python ignore coverage and add the replay-capture test module path to the focused validation commands in `specs/007-replay-observation-capture/quickstart.md`.

---

## Phase 2: Foundational

**Purpose**: Define the shared test fixtures and deterministic record surface required by all stories.

- [X] T002 Create red fixture helpers for qualified preparation, successful execution, frozen lane input, and a reporting backend in `tests/test_replay_capture.py`.
- [X] T003 Implement frozen replay-capture records, RFC 3339 validation, canonical hashing, and artifact evidence reduction in `isoprax/replay_capture.py`.

**Checkpoint**: The pure record surface is available; user-story reduction logic can be implemented and tested.

---

## Phase 3: User Story 1 - Capture a complete replay lane (Priority: P1) MVP

**Goal**: Retain a deterministic, attributable observed result for a complete eligible lane.

**Independent Test**: A qualified successful execution and complete successful backend response produce a full lineage record and the expected observed class; equivalent inputs share an identity and each material lane change differs.

- [X] T004 [US1] Write failing complete-lane, upstream-lineage, deterministic-identity, and material-input-change tests in `tests/test_replay_capture.py`.
- [X] T005 [US1] Implement qualification/execution eligibility checks, injected backend invocation, deployment validation, observation-window validation, and observed-positive/negative reduction in `isoprax/replay_capture.py`.
- [X] T006 [US1] Export the public replay-capture records and capture function from `isoprax/__init__.py`.

**Checkpoint**: A complete frozen lane is independently usable and produces only an attributable observed outcome.

---

## Phase 4: User Story 2 - Preserve censored lanes honestly (Priority: P1)

**Goal**: Retain exactly one explicit censored result for every unusable lane.

**Independent Test**: Build ineligibility, execution mismatch/failure, deployment failure/unverifiability/rollback/replacement, incomplete or invalid windows, and monitoring gaps each return `censored`, never `observed_negative`.

- [X] T007 [US2] Write failing censored-path and exactly-one-terminal-record tests in `tests/test_replay_capture.py`.
- [X] T008 [US2] Implement fail-closed censoring for upstream, backend, deployment, window, observation-validity, monitoring, and attribution failures in `isoprax/replay_capture.py`.

**Checkpoint**: Every requested lane has one terminal outcome and no missing data is converted into a negative outcome.

---

## Phase 5: User Story 3 - Audit a bounded replay capture (Priority: P2)

**Goal**: Retain auditable evidence identities while rejecting prohibited evidence sources.

**Independent Test**: Collected, missing, and unreadable artifacts are explicit; prohibited/missing evidence-scope declarations are censored; output exposes the frozen lineage and evidence-only claim scope.

- [X] T009 [US3] Write failing artifact-state, evidence-scope, audit-lineage, and claim-boundary tests in `tests/test_replay_capture.py`.
- [X] T010 [US3] Implement allowed-scope enforcement, artifact content identification, audit fields, and fixed evidence-only claim scope in `isoprax/replay_capture.py`.

**Checkpoint**: A reviewer can audit safe retained evidence and prohibited sources cannot become observed outcomes.

---

## Phase 6: Polish & Cross-Cutting Validation

**Purpose**: Verify the completed feature against its local and upstream contracts.

- [X] T011 Run focused replay-capture and upstream boundary tests from `tests/test_build_qualification.py`, `tests/test_hermetic_runner.py`, and `tests/test_replay_capture.py`.
- [X] T012 Run Ruff for `isoprax/replay_capture.py` and `tests/test_replay_capture.py`, then update completion markers in `specs/007-replay-observation-capture/tasks.md`.

## Dependencies & Execution Order

- T001 -> T002 -> T003
- T003 -> T004 -> T005 -> T006
- T005 -> T007 -> T008
- T005 and T008 -> T009 -> T010
- T006, T008, and T010 -> T011 -> T012

## Parallel Opportunities

- T004, T007, and T009 each modify the same focused test file, so execute them sequentially to preserve TDD evidence.
- The source implementation tasks all modify `isoprax/replay_capture.py`, so execute them sequentially.
- T006 can proceed after T005 while later test design begins, but it is small and should be reviewed with the public API.

## Implementation Strategy

1. Establish fixtures and immutable data validation.
2. Deliver the complete observed lane (US1) and prove deterministic identity.
3. Add every censoring path (US2) before adding optional evidence retention.
4. Enforce evidence scope and auditability (US3).
5. Run focused validation before convergence.
