# Tasks: Hermetic Replay Build Qualification

## Phase 1: Preparation contract

- [x] T001 [US1] Add failing preparation, legal-coverage, and runner-preflight tests in `tests/test_build_qualification.py`.
- [x] T002 [US1] Implement frozen sample, legal coverage, runner descriptor, and canonical preparation hash in `isoprax/build_qualification.py`.

## Phase 2: Execution evidence

- [x] T003 [US2] Add injected-runner classification tests in `tests/test_build_qualification.py`.
- [x] T004 [US2] Implement fail-closed runner invocation and immutable per-commit results in `isoprax/build_qualification.py`.

## Phase 3: Qualification reduction

- [x] T005 [US3] Add complete, partial, low-rate, and clustered-failure tests in `tests/test_build_qualification.py`.
- [x] T006 [US3] Implement complete-only measured-rate and claim-bounded report reduction in `isoprax/build_qualification.py`.

## Phase 4: Integration and validation

- [x] T007 Export the public qualification API from `isoprax/__init__.py`.
- [x] T008 Run focused tests, formatting, lint, and convergence checks.
