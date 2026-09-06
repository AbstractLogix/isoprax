# Tasks: Hermetic Runner Integration

## Phase 1: Setup

- [X] T001 Confirm the feature-005 preparation and injected-runner seam used by `isoprax/build_qualification.py` and record the narrow public boundary in `specs/006-hermetic-runner-integration/contracts/runner-backend.md`.

## Phase 2: Foundational contract

- [X] T002 Add failing configuration-validation and deterministic-identity tests in `tests/test_hermetic_runner.py`.
- [X] T003 Implement immutable configuration, effective-control, artifact-evidence, and execution-evidence records in `isoprax/hermetic_runner.py`.

## Phase 3: User Story 1 - Execute an approved recipe safely (Priority: P1)

**Goal**: Block unsafe or changed execution conditions before command start and invoke only a supplied approved backend.

**Independent Test**: A valid backend call receives frozen inputs; missing digest, root execution, writable source, unisolated work storage, enabled network, incomplete limits, or mismatched effective controls produces `blocked-before-compilation` without a command start.

- [X] T004 [US1] Add backend-invocation, preflight, and control-mismatch conformance tests in `tests/test_hermetic_runner.py`.
- [X] T005 [US1] Implement preparation validation, backend effect isolation, and blocked-before-compilation mapping in `isoprax/hermetic_runner.py`.

## Phase 4: User Story 2 - Preserve complete, attributable execution evidence (Priority: P1)

**Goal**: Retain immutable evidence and artifact states for every terminal attempt.

**Independent Test**: Controlled success, build failure, timeout, interruption, unavailable backend, and collected/missing/unreadable artifacts produce one complete record with the correct classification and content identity.

- [X] T006 [US2] Add terminal-classification and artifact-collection conformance tests in `tests/test_hermetic_runner.py`.
- [X] T007 [US2] Implement terminal classification, stable artifact hashes, and explicit collection states in `isoprax/hermetic_runner.py`.

## Phase 5: User Story 3 - Reproduce and audit an execution attempt (Priority: P2)

**Goal**: Bind execution evidence to its frozen preparation and applied controls deterministically.

**Independent Test**: Equivalent fixture inputs produce the same identity; each material change to revision, command, controls, limits, network policy, or mount disposition changes the identity or blocks the attempt.

- [X] T008 [US3] Add equivalence and material-control-change tests in `tests/test_hermetic_runner.py`.
- [X] T009 [US3] Implement canonical execution-identity derivation and provenance linkage in `isoprax/hermetic_runner.py`.

## Phase 6: Integration and validation

- [X] T010 Export the approved public runner records and execution entry point from `isoprax/__init__.py`.
- [X] T011 Update `specs/006-hermetic-runner-integration/quickstart.md` only if the final public call shape differs from its documented validation boundary.
- [X] T012 Run focused tests, lint, formatter checks, the documented synthetic demo, and Spec Kit convergence; record results in `specs/006-hermetic-runner-integration/converge.md`.

## Dependencies

```text
T001 -> T002 -> T003 -> T004/T005 -> T006/T007 -> T008/T009 -> T010 -> T012
```

User-story order is US1 -> US2 -> US3. US2 and US3 share the foundational
records and therefore follow US1's backend/preflight seam.

## Parallel Opportunities

- T004 and T006 can be drafted as distinct test sections once T003 defines the records.
- T008 can be drafted alongside T006 after T003; it depends only on the public identity fields, not artifact implementation.

## Implementation Strategy

1. Establish the fail-closed record and preflight boundary (MVP: US1).
2. Retain terminal and artifact facts without conflating artifact state with process outcome (US2).
3. Add deterministic audit identity and public export (US3).
4. Validate against feature 005 without introducing a container engine or a claim upgrade.
