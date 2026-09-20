---

description: "Task list for the optional EB-JEPA backend and efficacy gate"
---

# Tasks: EB-JEPA GPU Backend and Efficacy Gate

**Input**: Design documents from `/specs/037-eb-jepa-gpu-efficacy/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, and
`contracts/eb-jepa.md`

**Tests**: Included because the feature specification requires focused automated
conformance tests for optional runtime behavior and fail-closed evidence gates.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Declare the optional runtime without changing the base install.

- [x] T001 Add a `gpu` optional dependency group for the pinned PyTorch compatibility range in `pyproject.toml` and refresh `uv.lock` with `uv lock`
- [x] T002 [P] Add optional-runtime and claim-boundary notes to `README.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared feature helpers and evidence structures before story work.

- [x] T003 [P] Add raw deterministic event/state feature extraction helpers needed by both the NumPy and PyTorch JEPA paths in `isoprax/jepa.py`
- [x] T004 [P] Add immutable efficacy profile, per-family result, and report dataclasses in `isoprax/efficacy.py`
- [x] T005 [P] Add focused validation tests for split disjointness, profile thresholds, and fail-closed report serialization in `tests/test_eb_jepa_efficacy.py`

**Checkpoint**: Foundational types and validation rules are testable before backend integration.

---

## Phase 3: User Story 1 - Train the optional EB-JEPA backend (Priority: P1) 🎯 MVP

**Goal**: Fit a learned action-conditioned latent predictor on CPU or explicitly requested CUDA while preserving base import behavior.

**Independent Test**: With PyTorch installed, fit a bounded fixture twice on CPU and verify finite deterministic diagnostics and equivalent predictions; with CUDA available, verify the report records CUDA execution. Without PyTorch, the base suite still imports and passes.

### Tests for User Story 1

- [x] T006 [P] [US1] Add optional-backend contract tests for lazy import, malformed pairs, explicit missing-CUDA failure, deterministic CPU fit, and finite regularizer diagnostics in `tests/test_eb_jepa.py`
- [x] T007 [P] [US1] Add a CUDA smoke test that skips only when PyTorch/CUDA is unavailable and otherwise verifies actual CUDA device metadata in `tests/test_eb_jepa.py`

### Implementation for User Story 1

- [x] T008 [US1] Implement lazy PyTorch loading, explicit device validation, deterministic seeding, and `EBJEPAConfig`/`EBJEPATrainingReport` in `isoprax/eb_jepa.py`
- [x] T009 [US1] Implement change/state encoders, action-conditioned predictor, EMA target encoder, prediction loss, and variance/covariance anti-collapse diagnostics in `isoprax/eb_jepa.py`
- [x] T010 [US1] Implement fit-time backend identity, state representation identity, finite-loss rejection, prediction, risk, and anomaly readouts in `isoprax/eb_jepa.py`
- [x] T011 [US1] Export the optional backend types without eager PyTorch import in `isoprax/__init__.py`

**Checkpoint**: User Story 1 is independently usable as a runtime/implementation smoke test; it does not produce an efficacy claim.

---

## Phase 4: User Story 2 - Preserve shared readouts and provenance (Priority: P1)

**Goal**: Use the optional backend through the existing family-specific signal contracts and preserve Structural conformance boundaries.

**Independent Test**: Fit the backend, score both families, verify bounded signals and calibration behavior, and confirm shared backend provenance with no outcome pooling.

### Tests for User Story 2

- [x] T012 [P] [US2] Add risk/anomaly adapter tests for signal contracts, separate calibrators, backend identity, and missing anomaly context in `tests/test_eb_jepa.py`
- [x] T013 [P] [US2] Add conformance-boundary tests proving calibration and shared GPU code do not upgrade the default Structural assessment in `tests/test_eb_jepa.py`

### Implementation for User Story 2

- [x] T014 [US2] Implement EB-JEPA risk and anomaly strategy adapters over the existing `RiskStrategy`, `AnomalyStrategy`, `RiskSignal`, `AnomalySignal`, and `Calibrator` contracts in `isoprax/eb_jepa.py`
- [x] T015 [US2] Implement shared-readout provenance and Structural-only default assessment for the optional backend in `isoprax/eb_jepa.py`

**Checkpoint**: User Stories 1 and 2 are independently testable; no efficacy status is inferred from them.

---

## Phase 5: User Story 3 - Evaluate efficacy without overclaiming (Priority: P1)

**Goal**: Produce an auditable per-family claim status only when held-out evidence and predeclared thresholds pass.

**Independent Test**: Exercise missing data, leakage, one-class data, constant scores, baseline regression, and a passing two-family fixture; verify exact status and reasons.

### Tests for User Story 3

- [x] T016 [P] [US3] Add evaluator tests for missing/undersized/one-class/non-finite/constant/leaked evidence returning `not_claimable` in `tests/test_eb_jepa_efficacy.py`
- [x] T017 [P] [US3] Add evaluator tests for per-family baseline comparison, threshold versioning, scoped `efficacy_supported`, and no pooled cross-family score in `tests/test_eb_jepa_efficacy.py`

### Implementation for User Story 3

- [x] T018 [US3] Implement deterministic per-family AUC, Brier, ECE, class-count, baseline-gain, and threshold evaluation using existing diagnostics in `isoprax/efficacy.py`
- [x] T019 [US3] Implement split identity/leakage checks, completed-run checks, fail-closed reasons, scoped report identity, and status serialization in `isoprax/efficacy.py`
- [x] T020 [US3] Export efficacy profile/report/evaluator APIs in `isoprax/__init__.py`

**Checkpoint**: User Story 3 produces `not_claimable` for the current synthetic/smoke evidence and can produce `efficacy_supported` only for a fixture satisfying every predeclared gate.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete feature and document the evidence boundary.

- [x] T021 [P] Add a bounded synthetic demo/test fixture showing runtime evidence is not an efficacy claim in `tests/test_eb_jepa.py`
- [x] T022 Run focused backend/evaluator tests, the full pytest suite, Ruff, formatting, and pre-commit; record results in `specs/037-eb-jepa-gpu-efficacy/quickstart.md`
- [x] T023 Run Spec Kit convergence review and append any remaining implementation gaps to `specs/037-eb-jepa-gpu-efficacy/tasks.md`

## Phase 7: Review hardening

- [x] T024 Make malformed family evidence fail closed as report reasons instead of
  constructor exceptions, and add validated training/run provenance to reports
- [x] T025 Apply anti-collapse regularizers to trainable predictor outputs and add a
  regression test proving the weights affect predictions
- [x] T026 Add a torch-blocked base-import test and document `uv sync --extra gpu`
  as the reproducible optional-runtime path

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; optional dependency declaration only.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Stories (Phases 3-5)**: Depend on Foundational; US2 depends on the backend from US1, and US3 depends on backend/readout APIs from US1/US2.
- **Polish (Phase 6)**: Depends on all three user stories.

### Parallel Opportunities

- T002, T003, T004, and T005 can run in parallel where they touch different files.
- T006 and T007 can run in parallel; T012 and T013 can run in parallel; T016 and T017 can run in parallel.
- US3’s evaluator tests and backend tests are independent after the foundational types exist, but implementation integration follows the declared story order.

## Implementation Strategy

1. Keep the current NumPy backend as the always-available path.
2. Add the optional PyTorch backend and prove CPU/device behavior first.
3. Add shared adapters and provenance tests.
4. Add the evidence gate and verify that current synthetic data remains `not_claimable`.
5. Run the CUDA smoke test only if the host runtime is explicitly installed and usable.

**MVP**: Phase 3 (US1) demonstrates the optional learned backend and actual runtime
metadata. It is not a predictive efficacy claim.
