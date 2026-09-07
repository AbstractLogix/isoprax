---
description: "Implementation tasks for public label-semantics and split-sensitivity evidence"
---

# Tasks: Public Label-Semantics and Split-Sensitivity Evidence

**Input**: Design documents from `specs/015-public-label-semantics/`

## Phase 1: Foundation

- [X] T001 Extend `isoprax/public_label_evidence.py` with typed procedure and label-definition records, validation, and explicit unknown metadata.
- [X] T002 Add structured comparison statuses and deterministic report entities without changing the existing manifest reducer behavior.
- [X] T003 Export the new public contracts from `isoprax/__init__.py`.

## Phase 2: Evidence behavior

- [X] T004 Implement field-level comparison of structured Outcome Definitions with direct, bridgeable, irreducible, and unavailable outcomes.
- [X] T005 Require retained-observation evidence and provenance before reporting a bridgeable mismatch.
- [X] T006 Implement deterministic source ordering, duplicate/negative-input rejection, and report claim boundaries.
- [X] T007 Add a supplied manifest example under `examples/public-label-evidence/` documenting the offline and fail-closed boundary.

## Phase 3: Verification

- [X] T008 Add focused tests for metadata preservation, all comparison statuses, malformed records, blocked sources, and deterministic ordering.
- [X] T009 Run Ruff and focused tests, then the full pytest/coverage gate.
- [X] T010 Record implementation evidence and remaining deferred public-data questions in `specs/015-public-label-semantics/converge.md`.

## Dependencies

T001–T003 precede T004–T007. T008 follows the contract implementation. T009–T010 follow all code and documentation changes.
