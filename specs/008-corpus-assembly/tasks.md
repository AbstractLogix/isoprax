# Tasks: Replay Corpus Assembly

**Input**: Design documents from `/specs/008-corpus-assembly/`
**Tests**: Focused pytest conformance tests are required by the specification and Constitution III.

## Phase 1: Setup

- [X] T001 Verify existing Python ignore coverage and focused commands in `specs/008-corpus-assembly/quickstart.md`.

## Phase 2: Foundational

- [X] T002 Create red profile, capture, and score-time fixture helpers in `tests/test_corpus_assembly.py`.
- [X] T003 Implement immutable profile/input/rejection/report records and deterministic identity helpers in `isoprax/corpus_assembly.py`.

## Phase 3: User Story 1 - Assemble an auditable candidate corpus (Priority: P1)

- [X] T004 [US1] Write failing deterministic row, lineage, outcome-preservation, grouping, and ordering tests in `tests/test_corpus_assembly.py`.
- [X] T005 [US1] Implement capture-to-CorpusRow reduction and deterministic ordered report creation in `isoprax/corpus_assembly.py`.
- [X] T006 [US1] Export public corpus-assembly records and function in `isoprax/__init__.py`.

## Phase 4: User Story 2 - Refuse unsafe or inconsistent inputs (Priority: P1)

- [X] T007 [US2] Write failing rejection tests for foreign system, duplicate change, incomplete lineage, profile mismatch, field timing, and split/follow-up violations in `tests/test_corpus_assembly.py`.
- [X] T008 [US2] Implement fail-closed profile, lineage, field, scope, split, and duplicate-change rejection in `isoprax/corpus_assembly.py`.

## Phase 5: User Story 3 - Publish bounded assembly evidence (Priority: P2)

- [X] T009 [US3] Write failing manifest-input, class-count, unavailable-evidence, and evidence-only claim-boundary tests in `tests/test_corpus_assembly.py`.
- [X] T010 [US3] Implement safe manifest-input/count reduction and fixed claim boundary in `isoprax/corpus_assembly.py`.

## Phase 6: Validation

- [X] T011 Run focused capture, admission, and assembly tests in `tests/test_replay_capture.py`, `tests/test_stage1_admission.py`, and `tests/test_corpus_assembly.py`.
- [X] T012 Run Ruff and full CI-equivalent per-module coverage validation, then mark `specs/008-corpus-assembly/tasks.md` complete.

## Dependencies & Execution Order

- T001 -> T002 -> T003 -> T004 -> T005 -> T006
- T005 -> T007 -> T008
- T005 and T008 -> T009 -> T010 -> T011 -> T012

## Implementation Strategy

1. Define the immutable assembly boundary.
2. Deliver deterministic valid-row assembly.
3. Add fail-closed rejection coverage.
4. Add safe manifest evidence and verify the full repository gate.
