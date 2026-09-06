# Feature Specification: Replay Screening Refinement

**Feature Branch**: `004-replay-screening-refinement`
**Created**: 2026-09-05
**Status**: Complete

## Overview

003's measured historical-build gate is not a fair early candidate screen before a hermetic replay method exists. This refinement replaces it for early eligibility with a checkable reproducibility predictor. It does not measure historical builds or qualify replay execution.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Screen early eligibility from governing terms and reproducibility evidence (Priority: P1)

A reviewer receives a deterministic result without attempting historical builds.

**Independent Test**: Synthetic candidates lacking a governing source-build instrument, subject to a governing restriction, lacking an accepted hermeticity class, or supplying accepted evidence produce the required disposition.

**Acceptance Scenarios**:

1. **Given** multiple legal instruments, **When** the governing source-build instrument forbids benchmark publication or metric redistribution, **Then** Screen 2 rejects and retains that instrument's reference.
2. **Given** no retrievable governing source-build instrument, **When** a candidate is screened, **Then** Screen 2 rejects it.
3. **Given** accepted hermeticity evidence and an adequate estimated recent buildable window, **When** a candidate is screened, **Then** it can pass early eligibility without a historical build rate.
4. **Given** conventional or undocumented build evidence, **When** a candidate is screened, **Then** Screen 2.5 rejects before metadata evaluation.

### User Story 2 - Preserve the deferred verification boundary (Priority: P2)

An early-eligible candidate is never represented as historically build-qualified.

**Independent Test**: An eligible record declares the deferred qualification and caller-supplied build-rate data cannot change its early disposition.

## Edge Cases

- A permissive OSS licence is accompanied by a restrictive governing source-build term.
- A governing instrument lacks a reference.
- Hermeticity is asserted without evidence or a positive estimated window.
- An early-eligible candidate later fails measured qualification in the replay environment.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST screen in fixed order: estimated buildable-window supply, governing legal terms, replay-readiness prediction, then prediction-time metadata; it MUST stop after the first failure.
- **FR-002**: System MUST record every candidate's ordered results and early-eligibility disposition.
- **FR-003**: System MUST calculate Screen 1 supply from the estimated contiguous recent buildable window and observed or estimated positive-event rate, not full history.
- **FR-004**: System MUST require a retrievable legal instrument identified as governing the source-built artifact, record its type and reference, and reject restrictions on metric redistribution or benchmark publication.
- **FR-005**: System MUST accept only `pinned_distribution`, `hermetic_build`, or `pinned_container_toolchain` as replay-ready hermeticity classes. `conventional` or undocumented builds fail Screen 2.5.
- **FR-006**: System MUST mark early-eligible records `historical_build_rate_qualification_deferred` and MUST NOT use a historical build-success rate to decide early eligibility.
- **FR-007**: System MUST retain 003's prediction-time metadata allowlist as the final early screen.

### Key Entities

- **LegalInstrumentRecord**: type, reference, source-build applicability, and restrictions.
- **ReplayReadinessEvidence**: hermeticity class and evidence reference.
- **CandidateRecord**: early results, recorded evidence, and deferred measured-qualification state.

## Success Criteria *(mandatory)*

- **SC-001**: 100% of tested candidates without a retrievable applicable governing instrument fail Screen 2.
- **SC-002**: 100% of tested candidates with an unaccepted hermeticity class fail Screen 2.5 before metadata evaluation.
- **SC-003**: 100% of early-eligible records state the deferred measured-build qualification.
- **SC-004**: Equivalent inputs produce identical ordered screen results.

## Assumptions

- Reviewers supply evidence; the library does not retrieve legal documents.
- Estimated buildable windows are early-screen evidence, not measured build evidence.
- The replay-environment feature owns hermetic execution and historical build-rate qualification.

## Out of Scope

- Historical builds or replay execution.
- Candidate selection, external evidence verification, or changes to 002's allowlist/floor.
- Semantic or Full Conformance claims.

## Dependencies

- 002-stage1-corpus-admission supplies adequacy and metadata rules.
- 003-replay-candidate-selection supplies the screening baseline.
