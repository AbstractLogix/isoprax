# Feature Specification: Cross-Family Reference Kernel

**Feature Branch**: `001-cross-family-kernel`

**Created**: 2026-09-05

**Status**: Ready for Implementation

**Input**: User description: "Implement the Stage 0 Isoprax v0.3 reference kernel from the new
normative specification; use the supplied POC selectively and keep scope strictly Stage 0."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Normalize and assess both families (Priority: P1)

A researcher can submit a code-change event and an operational run event, receive their
respective probability signals, their declared outcome semantics, and whether the two scores are
permitted to be jointly compared.

**Why this priority**: This is the minimum proof that one contract governs both families while
preventing a false semantic-comparability claim.

**Independent Test**: Construct one valid event from each family, apply the matching strategy,
and verify a valid, family-aligned signal is returned.

**Acceptance Scenarios**:

1. **Given** a valid code-change event, **When** it is assessed, **Then** it produces a
   change-family risk signal with a score in the inclusive range zero to one.
2. **Given** a valid operational run event, **When** it is assessed, **Then** it produces an
   operational-family anomaly signal with a score in the inclusive range zero to one and a
   resolvable Outcome Definition.
3. **Given** a mismatched family discriminator or an invalid mandatory field, **When** the event
   is constructed, **Then** it is rejected rather than accepted under a false family.

---

### User Story 2 - Preserve evidence and feedback (Priority: P2)

A researcher can store an event, its signal, and the observed result, then retrieve the linked
history in time order for later calibration or evaluation.

**Why this priority**: Feedback is necessary for an honest conformance claim and future learning.

**Independent Test**: Persist a change or operational event with an extension field, signal, and
outcome; retrieve the linkage and verify the extension and ordering are unchanged.

**Acceptance Scenarios**:

1. **Given** a stored signal, **When** its observed outcome is recorded, **Then** the outcome
   references the originating event and exact producing strategy.
2. **Given** multiple stored events, **When** history is queried by family, type, or time range,
   **Then** matching records are returned in timestamp order without dropping extension data.

---

### User Story 3 - Make calibration status auditable (Priority: P3)

A researcher can evaluate probability signals against labeled outcomes and see whether they may be
called calibrated under the specification's fixed threshold.

**Why this priority**: Calibration and outcome commensurability are independent necessary
conditions for semantic interoperability.

**Independent Test**: Evaluate labeled scores and verify that the result reports ECE, Brier score,
bin reliability data, sample size, parameters, and the required calibrated/uncalibrated verdict.

**Acceptance Scenarios**:

1. **Given** fewer than 500 labeled events or ECE above 0.05, **When** calibration is checked,
   **Then** the result declares the scores uncalibrated.
2. **Given** at least 500 labeled events and ECE no greater than 0.05 in 10 equal-width bins,
   **When** calibration is checked, **Then** the result declares the scores calibrated.
3. **Given** two probability signals with non-commensurable Outcome Definitions, **When** a caller
   attempts pooling, ranking, thresholding, or joint reasoning, **Then** that operation is rejected
   and the signals remain separately scoped.

### Edge Cases

- A timestamp is malformed, non-UTC, or reused as an identifier.
- A forecast signal is offered a probability score, or a risk/anomaly signal is offered a
  forecast-only quantity.
- A signal or outcome refers to an event or Outcome Definition that was never stored.
- An Outcome is recorded under a different Outcome Definition from its originating Signal.
- Calibration data is empty, has unequal score/outcome lengths, or has only one outcome class.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST represent all accepted inputs as exactly one of ChangeEvent, RunEvent,
  or MetricSample, with a stable unique ID, RFC 3339 UTC timestamp, source, and type-derived family.
- **FR-002**: System MUST reject missing mandatory fields, invalid timestamps, and type/family
  mismatches; it MUST preserve permitted extension fields without silent loss.
- **FR-003**: System MUST provide change-risk and operational-anomaly strategy contracts whose
  signals have non-empty explanations, strategy provenance, family alignment, valid scores, and a
  resolvable identifier for the Outcome Definition the score predicts.
- **FR-004**: System MUST keep ForecastSignal probability-free and require its reported technique
  and a valid prediction interval.
- **FR-005**: System MUST persist and query events by ID, family, type, and time range; preserve
  event-to-signal-to-outcome associations; and expose ordered labeled history to strategies.
- **FR-006**: System MUST declare a probability signal uncalibrated unless the documented
  500-event, 10-bin, ECE-at-most-0.05 calibration test passes, and MUST expose its diagnostic data.
- **FR-007**: System MUST mechanically evaluate Outcome Definition commensurability using event,
  observation process, window, and thresholds; it MUST reject joint comparison or evaluation of
  non-commensurable scores and reject feedback labeled under a different definition.
- **FR-008**: System MUST provide time-sliced splitting and paired score-error comparison utilities
  for evaluation; it MUST not claim Full Conformance from the synthetic reference proof.
- **FR-009**: System MUST provide a reproducible synthetic demonstration of the two-family flow and
  document the honest Stage 0 boundary as Cross-Family Conformance (Structural), including why
  calibration does not upgrade non-commensurable definitions to Semantic conformance.

### Key Entities *(include if feature involves data)*

- **Event**: A normalized change or operational occurrence with immutable identity and origin.
- **Signal**: A strategy-produced assessment tied to one family and its provenance.
- **Outcome**: The observed result tied to the event and exact producing signal strategy.
- **Outcome Definition**: The declared event, observation process, window, and thresholds that
  make a probability score interpretable.
- **Calibration diagnostic**: Reliability bins, ECE, Brier score, evaluation size, and verdict.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Focused automated tests cover every functional requirement and pass on a clean
  checkout.
- **SC-002**: The demonstration completes offline and emits one persisted, linked flow for each
  family in a single run.
- **SC-003**: The calibration check reports all specified diagnostic fields and yields the required
  qualifier for both a passing and a failing synthetic input.
- **SC-004**: Documentation makes no claim beyond "Cross-Family Conformance (Structural)" unless
  reproducible evidence satisfies both the calibration and outcome-commensurability requirements.

## Assumptions

- The reference is an offline, local, synthetic Stage 0 artifact; real-data adapters are deferred.
- The supplied POC at the user-provided path is the authoritative v0.3 specification and Stage 0
  reference implementation; it supersedes the earlier v0.2 source.
- Deterministic replay, predeclaration, and evidence-boundary practices inform
  later roadmap phases; corpus-admission and JEPA/profile implementation are
  not automatically part of the Stage 0 kernel.

## Out of Scope (Stage 0)

- Real-data adapters, online serving, and any network-required runtime dependency.
- Semantic or Full Conformance claims.
- Automatic remediation/action-taking workflows.
- Importing third-party corpus-admission, JEPA/profile training/inference, or
  replay infrastructure as implementation dependencies.

## Readiness Gate

This feature is ready to continue implementation only when all of the following
remain true on a clean checkout:

- `tests/test_conformance.py` passes and covers all normative rules in this
  specification.
- Demo flow runs offline and reports Structural conformance only.
- Documentation preserves the claim boundary and explicitly withholds pooled
  cross-family figures when definitions are non-commensurable.
