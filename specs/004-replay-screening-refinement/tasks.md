# Tasks: Replay Screening Refinement

## Phase 1: Specification and tests

- [x] T001 Document the early-only scope in `specs/004-replay-screening-refinement/`.
- [x] T002 [US1] Add focused tests for legal instruments, estimated windows, and hermeticity evidence in `tests/test_replay_selection.py`.

## Phase 2: Implementation

- [x] T003 [US1] Add deterministic legal-instrument and replay-readiness validation in `isoprax/replay_selection.py`.
- [x] T004 [US1] Add `screen_early_candidate` with fail-fast ordering in `isoprax/replay_selection.py`.
- [x] T005 [US2] Record and test the deferred historical-build qualification state in `isoprax/replay_selection.py` and `tests/test_replay_selection.py`.

## Phase 3: Validation

- [x] T006 Run focused tests and static checks for touched files.
