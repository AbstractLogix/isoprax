# Feature Specification: Durable Knowledge-Base Integrity

**Feature Branch**: `019-kb-integrity`

## Summary

Harden the SQLite knowledge base so durable event, signal, outcome, and
Outcome Definition identities cannot be silently redefined or duplicated in a
way that changes the meaning of stored evidence.

## User Stories

### User Story 1 - Preserve durable definitions and events

As a researcher, I want a stored event or Outcome Definition identifier to
retain one meaning for its lifetime so historical scores remain interpretable.

**Acceptance scenarios**

1. Storing the same identifier with identical content is idempotent.
2. Storing the same identifier with different content is rejected and leaves
   the original content unchanged.

### User Story 2 - Preserve one signal identity

As an evaluator, I want one signal per event and strategy identity so a
calibration join cannot multiply one observed outcome into duplicate pairs.

**Acceptance scenarios**

1. Re-storing identical signal content is idempotent.
2. Re-storing different signal content for the same event and strategy is
   rejected.
3. The database enforces uniqueness for `(event_id, strategy_id)`.
4. Existing databases containing duplicate signal identities fail closed during
   migration instead of silently deleting or selecting rows.

## Functional Requirements

- **FR-001**: Replace event and Outcome Definition replacement writes with
  compare-before-write behavior.
- **FR-002**: Add a durable unique constraint for signal identity.
- **FR-003**: Keep the existing event → signal → outcome linkage behavior.
- **FR-004**: Make duplicate or conflicting writes produce actionable domain
  errors without mutating the original record.
- **FR-005**: Reject legacy duplicate signal rows when enabling the constraint.

## Claim Boundary

This feature protects evidence storage integrity. It does not establish
calibration, Semantic Conformance, or Full Conformance.
