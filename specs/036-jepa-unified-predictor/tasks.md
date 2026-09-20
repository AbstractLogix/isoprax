# Tasks: JEPA Unified Predictor

**Input**: Design documents from `/specs/036-jepa-unified-predictor/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, and `contracts/jepa-strategy.md`

**Tests**: Required by the project constitution and the feature acceptance criteria.

## Phase 1: Setup

- [x] T001 Verify the feature artifacts and existing NumPy/pytest toolchain in `specs/036-jepa-unified-predictor/` and `pyproject.toml`

## Phase 2: Foundational

- [x] T002 Define the immutable training/config/report/evidence data model in `isoprax/jepa.py`
- [x] T003 Define deterministic change and state encoders plus input validation in `isoprax/jepa.py`

## Phase 3: User Story 1 - Train a shared latent predictor (Priority: P1) 🎯 MVP

**Goal**: Fit an offline, deterministic action-conditioned predictor in latent space.

**Independent Test**: `uv run pytest -q tests/test_jepa.py -k 'training or deterministic or validation'`

- [x] T004 [P] [US1] Add deterministic training, malformed-input, and repeatability tests in `tests/test_jepa.py`
- [x] T005 [US1] Implement ridge-regularized latent predictor fitting and prediction in `isoprax/jepa.py`
- [x] T006 [US1] Add training report identity and finite latent-loss evidence in `isoprax/jepa.py`

## Phase 4: User Story 2 - Produce both readouts through the existing contract (Priority: P1)

**Goal**: Emit `RiskSignal` and `AnomalySignal` from one fitted backend while leaving calibration/admission unchanged.

**Independent Test**: `uv run pytest -q tests/test_jepa.py -k 'readout or calibration or persistence'`

- [x] T007 [P] [US2] Add signal, shared-backend, calibration, SQLite persistence, and admission-boundary tests in `tests/test_jepa.py`
- [x] T008 [US2] Implement JIT and AIOps readout adapters with existing strategy and signal contracts in `isoprax/jepa.py`
- [x] T009 [US2] Export the public JEPA types and outcome definitions from `isoprax/__init__.py`

## Phase 5: User Story 3 - Report conformance without overclaiming (Priority: P2)

**Goal**: Make the default Structural boundary explicit and gate Semantic status on validated evidence.

**Independent Test**: `uv run pytest -q tests/test_jepa.py -k 'conformance or semantic'`

- [x] T010 [P] [US3] Add fail-closed conformance evidence tests in `tests/test_jepa.py`
- [x] T011 [US3] Implement Structural/Semantic assessment validation and claim boundaries in `isoprax/jepa.py`

## Phase 6: Polish and validation

- [x] T012 [P] Update `specs/036-jepa-unified-predictor/quickstart.md` and public API documentation for the delivered surface
- [x] T013 Run focused and full tests, Ruff, formatting, and pre-commit checks; record only obtained evidence
- [x] T014 Run `speckit-converge`-equivalent review against `spec.md`, `plan.md`, and `tasks.md`; append no speculative work

## Dependencies and execution order

- T001 → T002/T003 → T004/T005/T006 → T007/T008/T009 → T010/T011 → T012/T013/T014.
- T004, T007, and T010 are test-first tasks for their story and may be prepared in parallel only when they do not modify the same file concurrently.
- User Story 2 depends on the fitted backend from User Story 1; User Story 3 depends on the shared identity from both readouts.

## Implementation strategy

1. Deliver the deterministic backend and its rejection tests as the MVP.
2. Add the two existing-contract readouts and verify SQLite/calibration/admission compatibility.
3. Add the conformance evidence gate and run repository-wide validation.
4. Keep GPU backend selection, real replay, and Semantic/Full efficacy claims out of this slice.
