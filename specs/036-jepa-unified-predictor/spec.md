# Feature Specification: JEPA Unified Predictor

**Feature Branch**: `036-jepa-unified-predictor`

**Created**: 2026-09-20

**Status**: Implemented (deterministic NumPy reference slice)

**Input**: Attached user specification: `Isoprax Feature Spec JEPA-Based Unified Predictor.md`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Train a shared latent predictor (Priority: P1)

As an Isoprax researcher, I can train one action-conditioned latent predictor from
change/state trajectory pairs without defect or incident labels, so that the
resulting model is usable for both readouts.

**Why this priority**: Self-supervised pretraining is the feature's foundation and
must remain usable before the calibration corpus is resolved.

**Independent Test**: Fit the predictor twice on the same deterministic pairs and
verify identical representation identity, parameters, prediction, and latent-loss
report. Fit must reject malformed or non-finite pairs.

**Acceptance Scenarios**:

1. **Given** valid change, pre-state, and post-state windows, **When** the model is
   trained, **Then** it returns a fitted report with a stable shared representation
   identity and finite latent prediction loss.
2. **Given** a pair with inconsistent state dimensions or non-finite values, **When**
   training starts, **Then** the model rejects it before fitting.

### User Story 2 - Produce both readouts through the existing contract (Priority: P1)

As an Isoprax researcher, I can obtain a JIT defect-risk probability from the change
representation and an AIOps failure-risk probability from latent prediction error,
so that both outputs use the existing `RiskSignal`/`AnomalySignal` and calibration
interfaces.

**Why this priority**: The value of the feature is the shared backend feeding both
families without changing admission or evaluation code.

**Independent Test**: Instantiate both adapters over one fitted backend, score a
change and evaluate an operational event with a complete pre/post window, and verify
that both signals are bounded, provenance-bearing, and separately calibratable.

**Acceptance Scenarios**:

1. **Given** a fitted backend and a change event, **When** the risk adapter scores it,
   **Then** it emits an existing-contract `RiskSignal` using only the change
   representation.
2. **Given** a fitted backend and pre/post operational windows, **When** the anomaly
   adapter evaluates the event, **Then** it emits an existing-contract
   `AnomalySignal` whose raw signal is derived from prediction error against the
   observed post-state representation.
3. **Given** an unfitted calibrator, **When** either adapter emits a signal,
   **Then** it declares the score uncalibrated; fitting a calibrator changes only
   calibration status/mapping, not the shared backend identity.

### User Story 3 - Report conformance without overclaiming (Priority: P2)

As an Isoprax reviewer, I can inspect the backend's representation and evidence
status, so that the implementation reports Structural conformance first and cannot
claim Semantic conformance merely because both scores are calibrated.

**Why this priority**: Honest conformance is a project requirement and the attached
spec explicitly gates the stronger claim on evidence that the representation is both
shared and non-decomposable.

**Independent Test**: Verify the default report is Structural, semantic evidence is
required and validated, and missing, mismatched, or decomposable evidence leaves the
report Structural.

**Acceptance Scenarios**:

1. **Given** a fitted backend without semantic evidence, **When** conformance is
   reported, **Then** the declarable tier is Structural and the claim boundary is
   included.
2. **Given** semantic evidence that does not identify the same backend or is marked
   decomposable, **When** conformance is reported, **Then** Semantic is withheld.
3. **Given** synthetic evidence with otherwise non-trivial readout values, **When**
   conformance is reported, **Then** Semantic is withheld until independently
   identified real-labeled evidence is supplied.

### Edge Cases

- Training with zero pairs, one pair, inconsistent dimensions, or non-finite values
  is rejected with a deterministic error.
- Scoring before training is rejected; anomaly evaluation without both pre- and
  post-state windows is rejected rather than inventing a score.
- A one-class JIT or AIOps calibration set remains uncalibrated under the existing
  `Calibrator` contract.
- Constant or non-finite prediction errors do not become a Semantic claim and must
  remain observable as insufficient evidence.
- GPU availability is not required for the reference PoC backend; accelerator-backed
  replacements remain behind the same strategy interfaces.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST represent a training example as one change action,
  one fixed-dimensional pre-change state window, and one fixed-dimensional
  post-change state window.
- **FR-002**: The system MUST train a predictor in representation space from those
  pairs without requiring bug or incident labels for pretraining.
- **FR-003**: The system MUST expose one stable backend identity and shared state
  representation identity to both readouts.
- **FR-004**: The JIT readout MUST derive its raw risk score from the change
  representation alone and emit the existing `RiskSignal` contract.
- **FR-005**: The AIOps readout MUST derive its raw failure score from the predictor
  error against the observed post-state representation and emit the existing
  `AnomalySignal` contract.
- **FR-006**: Both readouts MUST accept the existing calibration mechanism without
  changing admission, per-family evaluation, or calibration utilities.
- **FR-007**: The implementation MUST declare Structural conformance by default and
  MUST NOT declare Semantic conformance from calibration or shared code alone.
- **FR-008**: A Semantic claim MUST require independently identified real-labeled,
  validated evidence identifying the same non-decomposable representation and
  successful, non-trivial evidence for both readouts; synthetic evidence MUST leave
  the report Structural.
- **FR-009**: The reference implementation MUST be deterministic for identical
  inputs and MUST perform no network access during training or inference.
- **FR-010**: The implementation MUST preserve the existing admission floor and all
  existing strategy/signal persistence contracts; it MUST NOT lower or bypass the
  repository's current 800-row test-row gate.

### Key Entities

- **JEPA training pair**: A change action and its pre/post operational state
  windows; labels are not part of the pretraining entity.
- **Shared latent backend**: The change encoder, state encoder, action-conditioned
  predictor, fitted readout parameters, and immutable identity metadata.
- **Readout**: A family-specific projection from the shared backend to an existing
  probability Signal and Outcome Definition.
- **Conformance evidence**: Deterministic evidence that identifies the backend and
  demonstrates non-decomposable shared representation use for both readouts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Identical valid training pairs produce identical backend identity,
  parameters, predictions, and latent-loss report across repeated runs.
- **SC-002**: Every valid fitted backend can emit both a bounded JIT risk score and
  a bounded AIOps failure score through the existing signal contract without
  modifying calibration or admission code.
- **SC-003**: At least one focused test demonstrates that a calibration pass does
  not change the backend identity or upgrade the conformance tier.
- **SC-004**: The focused feature test suite covers all malformed-input rejection
  paths and passes together with the existing repository suite.
- **SC-005**: The implementation reports Structural conformance for the default
  PoC path and reports Semantic only when the explicit evidence gate passes.

## Assumptions

- The reference backend uses deterministic NumPy linear algebra; selecting or
  forking a GPU/deep-learning backend is a later implementation decision.
- Change text is optional in the normalized event; structured change fields remain
  sufficient for deterministic fallback encoding.
- A state window is an ordered sequence of `MetricSample` values with consistent
  dimensions represented through the existing event extension fields.
- JIT and AIOps Outcome Definitions remain separately declared and are not made
  commensurable by sharing a representation.
- The existing `Calibrator`, admission gate, per-family evaluation, and SQLite
  persistence remain the integration boundaries.
