# Tasks: Replay Candidate Selection and Predeclaration

## Phase 1: Setup and spec consistency

- [x] T001 Validate the feature directory and bootstrap the implementation scope for 003.
- [x] T002 Define the public API for screening, predeclaration, and exclusion records.

## Phase 2: Candidate screening core (TDD)

- [x] T003 Add tests for Screen 1 commit-supply adequacy failure.
- [x] T004 Add tests for Screen 2 licence/publication rejection.
- [x] T005 Add tests for Screen 3 build-rate and clustering rejection.
- [x] T006 Add tests for Screen 4 prediction-time metadata allowlist checks.
- [x] T007 Implement deterministic fixed-order candidate screening.

## Phase 3: Predeclaration provenance

- [x] T008 Add tests for artifact hash stability and tamper detection.
- [x] T009 Add tests for soak-duration training-only validation.
- [x] T010 Add tests for ancestry and external-anchor enforcement.
- [x] T011 Implement hash, ancestry, and anchor validation logic.

## Phase 4: Exclusion records and integration

- [x] T012 Add tests for structural and commensurability exclusions.
- [x] T013 Implement exclusion-record validation and replay justification support.
- [x] T014 Export the feature API from the package root and ensure compatibility wrappers exist.
- [x] T015 Run the full validation suite and confirm the feature is isolated from corpus collection or JEPA/profile scope.

## Requirement traceability notes

- Screening order and fail-fast semantics: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006
- Predeclaration integrity: FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013
- Exclusion structure: FR-014, FR-015, FR-016
