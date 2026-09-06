# Tasks: Stage 1 Per-Family Evaluation

**Input**: Design documents from `/specs/013-stage1-per-family-evaluation/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/per-family-evaluation.md`

**Tests**: Required by constitution contract-first testing.

## Phase 1: Setup

- [x] T001 Confirm `.specify/feature.json` points to `specs/013-stage1-per-family-evaluation`.
- [x] T002 Create feature artifacts: `research.md`, `data-model.md`, `quickstart.md`, `contracts/per-family-evaluation.md`, `tasks.md`, `converge.md`.

## Phase 2: Foundational

- [x] T003 Create `isoprax/per_family_evaluation.py` with profile/report dataclasses and canonical hashing helpers.
- [x] T004 Export public symbols in `isoprax/__init__.py`.

## Phase 3: User Story 1 (P1) — Reproducible per-family evidence

- [x] T005 [US1] Add deterministic fixture-based tests in `tests/test_per_family_evaluation.py`.
- [x] T006 [US1] Implement per-family metric and uncertainty reduction in `isoprax/per_family_evaluation.py`.
- [x] T007 [US1] Ensure explicit family/outcome-definition identity and non-pooling claim boundary in report payload.

## Phase 4: User Story 2 (P1) — Honest incomplete/blocked outcomes

- [x] T008 [US2] Add tests for blocked and inconclusive states in `tests/test_per_family_evaluation.py`.
- [x] T009 [US2] Implement unavailable-evidence derivation and status resolution logic.

## Phase 5: User Story 3 (P2) — Fail-closed policy

- [x] T010 [US3] Add tests for threshold mismatch, missing predeclaration, invalid score fields, and split-isolation violations.
- [x] T011 [US3] Implement fail-closed validation branches in `isoprax/per_family_evaluation.py`.

## Phase 6: Polish & Verification

- [x] T012 Run `make lint`, `make test`, and `make coverage`.
- [x] T013 Summarize verification outcomes in `specs/013-stage1-per-family-evaluation/converge.md`.
