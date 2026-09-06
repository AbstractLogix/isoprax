# Feature Specification: Shared Outcome Protocol

**Feature Branch**: `014-semantic-shared-outcome-protocol`  
**Status**: Draft

## Overview

Define and validate a predeclared shared outcome protocol that may make
separately collected family evidence eligible for semantic comparison. The
protocol establishes only the observation/label compatibility evidence; it does
not itself produce pooled scores or grant Semantic Conformance.

## User Scenarios & Testing

### User Story 1 - Review a shared outcome definition (Priority: P1)

A reviewer can compare two declared family protocols and determine whether the
event, observation process, window, threshold, censoring policy, and release
scope are genuinely shared.

**Acceptance Scenarios**:

1. Equivalent declarations produce the same protocol identity and compatibility
   verdict.
2. Any event, window, threshold, censoring, provenance, or scope mismatch is
   explicitly rejected as non-commensurable.
3. A compatible verdict states that pooled evaluation remains a later,
   separately evidenced step.

## Requirements

- **FR-001**: Require predeclared shared event, observation process, window,
  threshold, censoring policy, provenance, and release scope.
- **FR-002**: Deterministically compare each named element and expose the exact
  mismatch categories without raw restricted data.
- **FR-003**: Reject post-collection declarations, mutable threshold changes,
  private/privileged provenance, and partial compatibility assertions.
- **FR-004**: Fix the output boundary to protocol-compatibility evidence only;
  it MUST NOT state Semantic/Full Conformance or pooled performance.

## Success Criteria

- **SC-001**: Every tested mismatch is reported with a deterministic category.
- **SC-002**: Compatible fixtures never produce a conformance-class upgrade.

## Out of Scope

- Pooling metrics, cross-family model evaluation, real corpus acquisition, and
  automated policy or remediation.
