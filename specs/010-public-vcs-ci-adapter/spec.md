# Feature Specification: Public VCS/CI Evidence Adapter

**Feature Branch**: `010-public-vcs-ci-adapter`  
**Status**: Draft

## Overview

Provide a read-only, deterministic adapter that normalizes explicitly supplied
public VCS and CI evidence for one selected system into the existing replay
candidate and build-qualification boundaries. It never retrieves credentials,
private repositories, or telemetry, and does not collect a corpus, execute a
replay, admit evidence, or make a conformance claim.

## User Scenarios & Testing

### User Story 1 - Normalize public source evidence (Priority: P1)

A reviewer can supply a frozen public evidence snapshot and receive canonical
candidate/build inputs with explicit freshness and completeness status.

**Acceptance Scenarios**:

1. Given equivalent public snapshots in different orders, when normalized, then
   identifiers and ordered records are identical.
2. Given missing, stale, non-public, or contradictory source/CI evidence, when
   normalized, then it is rejected or explicitly unavailable.

### User Story 2 - Preserve publication boundaries (Priority: P1)

A reviewer can inspect safe references and hashes without repository payloads,
credentials, private URLs, logs, or CI secrets.

**Acceptance Scenarios**:

1. Given a normalized record, when rendered for review, then it contains only
   public safe references, hashes, timestamps, and declared availability.
2. Given an attempt to use it as replay/admission evidence, then its claim
   boundary states candidate/build-preparation evidence only.

## Requirements

- **FR-001**: The adapter MUST accept only explicitly supplied public evidence
  snapshots and MUST perform no network I/O.
- **FR-002**: The adapter MUST require immutable source revision, public source
  reference, CI evidence reference, observation timestamp, and provenance.
- **FR-003**: The adapter MUST deterministically normalize, sort, and identify
  valid records; missing or stale required evidence MUST be explicit.
- **FR-004**: The adapter MUST reject private/credential-bearing references,
  privileged telemetry, mutable-only source references, and contradictory
  revision/CI linkage.
- **FR-005**: The output MUST be limited to candidate/build-preparation evidence
  and MUST not assert qualification, replay success, corpus admission, or any
  conformance class.

## Success Criteria

- **SC-001**: Equivalent valid snapshots produce identical canonical output in
  100% of deterministic test runs.
- **SC-002**: 100% of tested private, mutable, stale, and contradictory inputs
  are rejected or explicitly unavailable without a misleading success result.

## Out of Scope

- Network clients, repository cloning, CI execution, secret handling, corpus
  collection, telemetry, replay, admission, and conformance claims.
