# Feature Specification: Hermetic Replay Build Qualification

**Feature Branch**: `005-replay-build-qualification`
**Created**: 2026-09-05
**Status**: Draft

## Overview

This feature supplies the measured historical-build evidence intentionally deferred by 004. A reviewer prepares a fixed historical sample, verifies each revision's legal coverage, runs only authorized revisions in a constrained hermetic environment, and receives a deterministic qualification result. It establishes build evidence only; it does not collect a corpus, select a candidate, or establish conformance.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prepare a reproducible build sample (Priority: P1)

A reviewer submits an ordered, predeclared commit sample and a runner description. The system records a content-addressed preparation artifact and refuses compilation if any revision lacks required legal coverage or the runner is not immutable.

**Why this priority**: No build result is trustworthy without a fixed input and an attributable execution environment.

**Independent Test**: A fixed synthetic sample with complete coverage produces a stable preparation hash; a missing licence record or mutable runner yields `blocked-before-compilation` and no invocation.

**Acceptance Scenarios**:

1. **Given** a sample with complete per-revision legal coverage and an immutable runner, **When** preparation runs twice, **Then** it produces the same preparation hash and row order.
2. **Given** any sampled revision without legal coverage, **When** qualification is requested, **Then** every affected row is `blocked-before-compilation` and the runner is not invoked.
3. **Given** a runner named only by a mutable tag, **When** preparation runs, **Then** qualification is blocked.

### User Story 2 - Execute and reduce historical build evidence (Priority: P1)

A reviewer runs an authorized prepared sample and receives one deterministic result per revision: `success`, `censored`, or `blocked-before-compilation`.

**Why this priority**: Qualification must preserve failures and environmental interruptions instead of silently dropping them.

**Independent Test**: An injected runner emits success, build failure, and infrastructure interruption; the result retains all rows and produces the documented classifications.

**Acceptance Scenarios**:

1. **Given** an authorized row whose build succeeds, **When** the runner returns success, **Then** that row is recorded as `success`.
2. **Given** an authorized row whose build fails, **When** the runner returns a build failure, **Then** that row is recorded as `censored`, not deleted or treated as success.
3. **Given** an unavailable runner or invalid execution setup, **When** qualification runs, **Then** the row is recorded as `blocked-before-compilation` with a reason.

### User Story 3 - Qualify only complete, unbiased measurements (Priority: P2)

A reviewer receives a build-rate decision only when all predeclared rows have execution outcomes and temporal failure clustering is evaluated.

**Independent Test**: A complete sample exceeding its frozen floor passes; an incomplete, low-rate, or temporally clustered sample fails with an explicit reason.

**Acceptance Scenarios**:

1. **Given** a complete result set with enough successful builds and no clustered failures, **When** reduction runs, **Then** it records measured qualification.
2. **Given** a blocked or unexecuted row, **When** reduction runs, **Then** it reports qualification unavailable rather than estimating a rate.
3. **Given** failures clustered in time, **When** reduction runs, **Then** it fails qualification even if the aggregate rate meets the floor.

## Edge Cases

- Duplicate commits, an empty sample, or a changed sample order after predeclaration.
- A record claims source coverage but contains no retrievable licence reference.
- A runner has a digest but no writable non-root work area.
- A build process times out or exits before compilation starts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST require an ordered, duplicate-free predeclared commit sample and record a content hash over the sample, legal records, runner identity, and build recipe.
- **FR-002**: System MUST require a retrievable legal-coverage record for every sampled revision before any runner invocation; missing coverage produces `blocked-before-compilation`.
- **FR-003**: System MUST require an immutable runner identity and a constrained non-root execution description with writable work storage before execution.
- **FR-004**: System MUST execute only through an injected runner boundary and record one immutable row result for every predeclared revision.
- **FR-005**: System MUST classify rows as `success`, `censored`, or `blocked-before-compilation`; failures, timeouts, and interrupted builds MUST NOT be removed.
- **FR-006**: System MUST reject a qualification measurement unless every predeclared row has an execution outcome; it MUST not derive a rate from a partial sample.
- **FR-007**: System MUST calculate the measured success rate against the complete predeclared sample, compare it with the frozen candidate floor, and reject temporal failure clustering.
- **FR-008**: System MUST label every output as build-qualification evidence only and MUST NOT upgrade any Isoprax conformance class.

### Key Entities

- **BuildSample**: ordered commits, frozen build recipe, legal records, runner identity, and preparation hash.
- **LegalCoverageRecord**: revision, retrievable governing reference, and coverage disposition.
- **RunnerDescriptor**: immutable identity plus non-root and writable-work guarantees.
- **BuildRowResult**: one revision's terminal classification and diagnostic evidence.
- **BuildQualificationReport**: complete sample result, success rate when available, clustering decision, and claim boundary.

## Success Criteria *(mandatory)*

- **SC-001**: Equivalent valid preparation inputs produce the same hash and ordered rows in 100% of test runs.
- **SC-002**: 100% of samples with missing legal coverage are blocked before runner invocation.
- **SC-003**: 100% of qualification reports retain one row for each predeclared revision.
- **SC-004**: No incomplete sample emits a measured success rate or qualified disposition.

## Assumptions

- Candidate selection, legal research, the frozen build floor, and the replay recipe are supplied by prior predeclaration and screening work.
- An integration later provides the actual container or sandbox runner; this feature validates the runner contract and can be proven with an injected deterministic runner.

## Out of Scope

- Discovering a candidate, downloading source, or retrieving licences over the network.
- Runtime soak, deployment, outcome observation, corpus admission, model evaluation, or conformance claims.

## Dependencies

- 003 supplies predeclaration provenance and frozen build-floor semantics.
- 004 supplies early eligibility and the deferred measured-qualification boundary.
