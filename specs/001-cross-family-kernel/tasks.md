# Tasks: Cross-Family Reference Kernel

## Phase 1: Setup

- [x] T001 Add Python packaging, uv development dependencies, and ignore rules in `pyproject.toml` and `.gitignore`
- [x] T002 Add Apache-2.0 licensing and contributor guidance in `LICENSE` and `CONTRIBUTING.md`
- [x] T003 Add local AI/workflow guidance and Codex Spec Kit integration in `AGENTS.md` and `.agents/skills/`
- [x] T004 Add pre-commit quality and secret-detection checks in `.pre-commit-config.yaml`

## Phase 2: Foundational Contract

- [x] T005 Copy and lint the normalized event, signal, Outcome Definition, KB, strategy, and evaluation modules in `isoprax/`
- [x] T006 Verify Outcome feedback cannot use a definition different from its originating signal in `isoprax/kb.py`

## Phase 3: User Story 1 - Normalize and assess both families

- [x] T007 [US1] Copy baseline Change and Operational strategies in `isoprax/baseline_strategies.py`
- [x] T008 [US1] Copy contract coverage for event and signal validity in `tests/test_conformance.py`

## Phase 4: User Story 2 - Preserve evidence and feedback

- [x] T009 [US2] Copy SQLite persistence and linkage coverage in `isoprax/kb.py` and `tests/test_conformance.py`

## Phase 5: User Story 3 - Make calibration status auditable

- [x] T010 [US3] Copy synthetic calibration and commensurability demonstration in `examples/demo_cross_family.py`
- [x] T011 [US3] Verify Ruff, tests, demo, and pre-commit from `README.md`

## Phase 6: Documentation and convergence

- [x] T012 Update the Stage 0 run and claim boundary in `README.md`
- [x] T013 Record plan, data model, contract, quickstart, and convergence evidence under `specs/001-cross-family-kernel/`

## Phase 7: Convergence

- [x] T014 CRITICAL Enforce non-empty IDs and sources, RFC 3339 UTC timestamps, and accepted concrete event types, with malformed/non-UTC rejection tests per FR-001 and FR-002 (contradicts).
- [x] T015 CRITICAL Keep the Stage 0 cross-family report Structural-only and reject Semantic or Full declarations from synthetic inputs per FR-008, FR-009, and Constitution II (contradicts).
- [x] T016 Add focused calibration conformance tests and explicit input validation for empty, unequal, and single-class labels per FR-006 and SC-003 (partial).
- [x] T017 Add focused time-sliced and paired-comparison tests, including rejection paths, per FR-008 and SC-001 (partial).
- [x] T018 Update the completed feature status and convergence evidence with the obtained validation result per T013 (partial).
