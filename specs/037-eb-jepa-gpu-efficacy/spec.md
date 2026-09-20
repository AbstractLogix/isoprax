# Feature Specification: EB-JEPA GPU Backend and Efficacy Gate

**Feature Branch**: `037-eb-jepa-gpu-efficacy`

**Created**: 2026-09-20

**Status**: Implemented; efficacy evidence remains not claimable pending real labeled data

**Input**: User request to implement an EB-JEPA/GPU backend and determine whether an efficacy claim is supportable.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Train the optional EB-JEPA backend (Priority: P1)

As an Isoprax researcher, I can train an optional PyTorch backend on the existing
JEPA training-pair contract, using an accelerator when explicitly requested, so
that the project has a GPU-capable learned predictor without changing the existing
deterministic NumPy backend.

**Why this priority**: A GPU-capable learned backend is the requested capability and
is a prerequisite for any meaningful held-out efficacy evaluation.

**Independent Test**: With PyTorch available, fit the backend twice on the same
bounded fixture and verify finite losses, a stable configuration identity, and
equivalent predictions. With no PyTorch installed, importing the base package and
running the existing suite must still work.

**Acceptance Scenarios**:

1. **Given** valid training pairs and an available requested device, **When** the
   backend is fitted, **Then** it reports the device actually used, finite training
   diagnostics, and a stable backend identity.
2. **Given** `device="cuda"` but no usable CUDA-enabled PyTorch runtime, **When** fit
   starts, **Then** it fails closed with an actionable dependency/device error rather
   than silently claiming GPU execution.
3. **Given** the existing NumPy backend, **When** the optional backend is absent,
   **Then** the NumPy backend and its public strategy contracts remain unchanged.

---

### User Story 2 - Preserve shared readouts and provenance (Priority: P1)

As an Isoprax researcher, I can use the GPU backend through the same separate JIT
risk and AIOps anomaly readouts, so that a backend change does not turn two
non-commensurable outcomes into one unsupported score.

**Why this priority**: Shared-backend provenance is the existing feature contract;
accelerator support is not useful if it bypasses the signal, calibration, or
conformance boundaries.

**Independent Test**: Fit the backend, score both readout families, and verify that
each signal is bounded, separately calibratable, and traceable to the same backend
identity while the default conformance tier remains Structural.

**Acceptance Scenarios**:

1. **Given** a fitted backend and a change event, **When** the risk adapter scores it,
   **Then** it emits the existing `RiskSignal` contract with backend provenance.
2. **Given** a fitted backend and complete pre/post operational windows, **When** the
   anomaly adapter scores the event, **Then** it emits the existing `AnomalySignal`
   contract with backend provenance.
3. **Given** either readout, **When** its calibration is fitted, **Then** only that
   family’s calibration mapping changes; backend identity and outcome commensurability
   do not change.

---

### User Story 3 - Evaluate efficacy without overclaiming (Priority: P1)

As an Isoprax reviewer, I can run a predeclared held-out evaluation against a named
baseline and receive an explicit claim status, so that a GPU experiment produces an
efficacy claim only when the evidence supports it.

**Why this priority**: The requested “see if we can make an efficacy claim” is an
evidence question, not a license to treat a successful training run or synthetic
smoke test as predictive validation.

**Independent Test**: Run the evaluator on (a) an undersized or single-split fixture,
   (b) a valid held-out two-class fixture where the backend does not beat the
   baseline, and (c) a fixture satisfying all declared thresholds. Verify the first
   two return `not_claimable` with reasons and the last returns `efficacy_supported`
   with per-family metrics and evidence metadata.

**Acceptance Scenarios**:

1. **Given** no held-out labeled data, **When** evaluation runs, **Then** it returns
   `not_claimable` and names the missing evidence.
2. **Given** held-out labels with only one class, leakage, non-finite scores, or a
   missing baseline, **When** evaluation runs, **Then** it returns `not_claimable`
   and does not substitute neutral values.
3. **Given** independent train/calibration/test partitions, a named baseline, both
   classes in each family, finite non-degenerate scores, and predeclared improvement
   and calibration thresholds met for both families, plus a validated completed
   training report, canonical run configuration, and independently verified
   digest-backed real-labeled provenance, **When** evaluation runs, **Then** it returns
   `efficacy_supported` only for the evaluated corpus, model, split, run, and
   outcome definitions.
4. **Given** valid per-family results but different Change and Operational outcome
   definitions, **When** the report is produced, **Then** it does not emit a pooled
   cross-family efficacy score or a Semantic/Full Conformance claim.

---

No additional user stories are required; the three prioritized journeys above cover
the optional backend, shared readouts, and the evidence-gated efficacy decision.

### Edge Cases

- PyTorch is not installed: the base package remains importable and GPU-only tests
  are skipped or reported as unavailable; no GPU claim is emitted.
- CUDA is visible but initialization fails: requested CUDA execution fails closed and
  reports the runtime error category.
- A CPU device is explicitly selected: the backend may run for deterministic tests,
  but the report marks the run as CPU and cannot call it GPU evidence.
- Training has zero pairs, inconsistent dimensions, non-finite values, or one sample:
  fitting rejects the input deterministically.
- A run is stopped before completing the declared epochs or produces non-finite loss:
  evaluation is not claimable.
- Train, calibration, and test identifiers overlap: evaluation rejects the run as
  leakage rather than attempting to repair the split.
- One family has a one-class test set, constant scores, or invalid probabilities:
  only that family fails and the overall efficacy status remains `not_claimable`.
- A model improves one family but regresses the other, or misses any predeclared
  threshold: the overall claim remains `not_claimable`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an optional EB-JEPA-style PyTorch backend that
  consumes the existing normalized training-pair contract and is importable without
  importing PyTorch when the optional dependency is absent.
- **FR-002**: The backend MUST expose explicit device selection and MUST report the
  actual runtime device, PyTorch version, CUDA availability, and deterministic seed
  in its training report.
- **FR-003**: A requested CUDA run MUST fail closed when CUDA-enabled PyTorch cannot
  be imported or initialized; it MUST NOT silently downgrade to CPU.
- **FR-004**: The backend MUST use a shared learned state representation for its
  action-conditioned prediction and both readouts, and MUST expose a stable backend
  identity for provenance.
- **FR-005**: The backend MUST include an anti-collapse regularization diagnostic and
  MUST reject or mark a run invalid when the training loss or required diagnostics
  are non-finite.
- **FR-006**: The GPU backend MUST preserve the existing `RiskSignal`,
  `AnomalySignal`, `Calibrator`, Outcome Definition, and persistence contracts.
- **FR-007**: The evaluator MUST require explicit, disjoint train/calibration/test
  partitions, a named baseline, both outcome classes per evaluated family, finite
  scores, a validated completed training report tied to the model identity, a
  canonical run configuration tied to that backend, and a completed run before
  producing efficacy evidence.
- **FR-008**: The evaluator MUST compare the GPU backend with the named baseline per
  family using predeclared thresholds for discrimination and calibration; thresholds
  MUST be recorded in the report rather than inferred after seeing results.
- **FR-009**: The evaluator MUST return an explicit claim status and machine-readable
  failure reasons; malformed, absent, unverified, or insufficient evidence MUST be
  represented as `not_claimable` rather than raising during metric evaluation.
- **FR-010**: A successful evaluator report MUST scope any efficacy claim to the
  corpus identity, split identity, model/backend identity, run configuration,
  validated training report, independently verified digest-backed evidence
  provenance, outcome definitions, and metrics actually evaluated. The report
  identity MUST cover that complete scope.
- **FR-011**: The evaluator MUST NOT pool or rank the separate Change and Operational
  outcomes when the existing commensurability check does not permit it.
- **FR-012**: Synthetic fixtures and GPU smoke tests MUST be labeled implementation
  evidence only and MUST NOT satisfy the project’s real-data efficacy or Stage 2
  admission claim by themselves.
- **FR-013**: Existing deterministic NumPy behavior, the repository’s current
  admission floor, and all existing tests MUST remain intact. A claimable profile
  MUST preserve the protected floor of at least 800 test rows, 50 positive events,
  and 50 negative events per family; lower fixture thresholds remain
  `not_claimable`.

### Key Entities

- **EB-JEPA training report**: Completed/failed run metadata, backend identity, device,
  seed, regularization diagnostics, and finite-loss status.
- **Efficacy evaluation profile**: Named baseline, disjoint split identities,
  thresholds, minimum evidence requirements, and outcome-family scope.
- **Per-family efficacy result**: Held-out discrimination and calibration metrics,
  baseline comparison, sample/class counts, and failure reasons.
- **Efficacy claim report**: A fail-closed status (`not_claimable` or
  `efficacy_supported`) plus the exact evidence scope and per-family results.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On an optional-dependency fixture, the backend completes a bounded fit
  on the requested device, reports finite loss/regularizer diagnostics, and emits
  stable repeated-run predictions.
- **SC-002**: The existing suite passes with PyTorch absent; when PyTorch is present,
  focused GPU-backend tests pass without changing the NumPy backend’s results.
- **SC-003**: Every insufficient-evidence fixture returns `not_claimable` with at
  least one actionable reason; no synthetic smoke test is reported as efficacy.
- **SC-004**: A fixture meeting every predeclared gate returns a scoped
  `efficacy_supported` result for both evaluated families, while a fixture failing
  any one family gate returns `not_claimable` overall.
- **SC-005**: The report contains the baseline, split, model, outcome-definition,
  threshold, sample-count, calibration, and discrimination provenance needed for an
  independent reviewer to reproduce the decision.
- **SC-006**: The implementation never emits a pooled Change/Operational efficacy
  score or upgrades the existing Structural conformance boundary from this feature.

## Assumptions

- The GPU backend is an optional research/reference path; the project’s base install
  remains dependency-light and CPU-capable.
- The project will not vendor or reproduce the full external EB-JEPA repository;
  this feature adapts its relevant energy-based predictive concepts to Isoprax’s
  existing tabular/event contract.
- The external EB-JEPA repository and its published experiments are references for
  architecture and training hygiene, not evidence about Isoprax efficacy.
- The default proof fixture is synthetic and bounded. Real-data efficacy requires a
  separately identified, access-controlled corpus and independent labels.
- Thresholds are supplied by the evaluation profile before test scores are computed;
  this feature does not invent scientific thresholds from one observed run.
- A GPU benchmark may be reported as runtime/device evidence, but speedup is not an
  efficacy claim and is out of scope unless a benchmark profile is supplied.
