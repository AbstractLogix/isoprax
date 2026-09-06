# Feature Specification: Public Operational Evidence Adapter

**Feature Branch**: `011-public-telemetry-adapter`  
**Status**: Draft

## Overview

Normalize an explicitly supplied, public operational-evidence snapshot for one
system into a deterministic observation input. This feature is distinct from
VCS/CI evidence because it handles declared observation windows and public
operational artifacts; it never contacts telemetry services or treats missing
data as an observed negative outcome.

## User Scenarios & Testing

### User Story 1 - Normalize a declared public observation (Priority: P1)

A reviewer receives a canonical public observation record with its window,
threshold metadata, artifact availability, freshness, and explicit censoring.

**Independent Test**: Reduce the same valid snapshot twice (including with reordered fields) and verify the canonical public record and identity are identical; submit a snapshot with private/privileged material and verify it is rejected or retained only as explicit unavailability/censoring.

**Acceptance Scenarios**:

1. Equivalent snapshots produce identical public records and identities.
2. Missing, stale, incomplete, invalid, private, or privileged observations
   become explicit unavailability/censoring rather than a negative outcome.

## Requirements

- **FR-001**: The system MUST accept only supplied public observation metadata and MUST perform no network access.
- **FR-002**: The system MUST require a frozen window, threshold rule, source reference, provenance, and public artifact declaration.
- **FR-003**: The system MUST reject private production data, privileged telemetry, credential-bearing references, post-window material, and contradictory timestamps.
- **FR-004**: The system MUST preserve unavailable/incomplete evidence as explicit censoring or availability state, and MUST NOT infer an observed-negative outcome.
- **FR-005**: The system MUST state an observation-evidence-only claim boundary and MUST NOT grant replay completion, admission, or conformance.

## Success Criteria

- **SC-001**: Equivalent valid snapshots yield identical canonical records.
- **SC-002**: All tested scope and window violations fail closed.

## Out of Scope

- Telemetry clients, production credentials, private data, replay execution,
  corpus assembly, admission, and conformance claims.
