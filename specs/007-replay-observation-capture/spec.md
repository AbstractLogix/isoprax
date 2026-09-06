# Feature Specification: Replay Observation Capture

**Feature Branch**: `007-replay-observation-capture`
**Created**: 2026-09-06
**Status**: Ready for planning
**Input**: User description: "start spec 007"

## Overview

This feature turns a predeclared, build-qualified replay lane into auditable deployment and outcome-observation evidence. For one clean revision in one system, a reviewer can retain an immutable chain from approved execution through deployment to a complete observation window. A failed build or deployment, incomplete follow-up, invalid lineage, or monitoring gap is retained as censored evidence. The feature establishes neither corpus admission nor an Isoprax conformance class.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capture a complete replay lane (Priority: P1)

A reviewer runs a predeclared single-service workload for one eligible revision and receives a linked deployment and outcome record once its full observation window completes.

**Why this priority**: Stage 1 cannot safely assemble a replay corpus unless every usable outcome can be traced to one authorized change, build, deployment, and frozen observation definition.

**Independent Test**: A controlled qualified execution, deployment result, and complete telemetry window produce one deterministic lineage-complete observed record whose stored workload, horizon, outcome rule, and capture schema match the predeclaration.

**Acceptance Scenarios**:

1. **Given** an eligible successful execution and a complete frozen lane definition, **When** its deployment and observation window complete, **Then** the capture retains linked execution, deployment, and observation evidence with exactly one observed outcome classification.
2. **Given** two otherwise equivalent capture requests, **When** they use the same frozen lane definition and source evidence, **Then** they derive the same lane identity and evidence references.
3. **Given** a capture request with a changed revision, service, workload, horizon, threshold rule, or schema, **When** it is evaluated, **Then** it is identified as a different lane rather than merged with prior evidence.

---

### User Story 2 - Preserve censored lanes honestly (Priority: P1)

A reviewer can distinguish a missing or unusable replay result from an observed negative outcome and can inspect why the lane was censored.

**Why this priority**: Treating operational failure or incomplete follow-up as an outcome would bias later corpus admission and evaluation.

**Independent Test**: Controlled build failure, deployment failure, missing telemetry, and incomplete-window inputs each retain one censored lane with the applicable reason; none becomes an observed-negative row.

**Acceptance Scenarios**:

1. **Given** an execution that cannot produce a deployable successful build, **When** capture is requested, **Then** the lane is censored before deployment and names the build evidence that caused the censoring.
2. **Given** a failed or unverifiable deployment, **When** capture completes, **Then** the lane is censored and no observed outcome is emitted.
3. **Given** a telemetry gap, invalid observation evidence, or an observation window that cannot complete under its frozen horizon, **When** capture is reduced, **Then** the lane is censored with an explicit reason.

---

### User Story 3 - Audit a bounded replay capture (Priority: P2)

A reviewer can inspect the facts needed to reproduce the interpretation of a lane without exposing private production data or privileged telemetry.

**Why this priority**: Replay evidence is useful only if its provenance and claim boundary are inspectable while remaining safe to retain and publish.

**Independent Test**: A capture record with permitted evidence exposes its predeclaration, lineage, times, outcome class, evidence identities, and claim scope; a request containing a prohibited data source is rejected or censored before it is retained as observation evidence.

**Acceptance Scenarios**:

1. **Given** a retained replay lane, **When** a reviewer requests its audit record, **Then** they can trace the frozen definition and execution, deployment, and observation evidence identities without relying on timing proximity alone.
2. **Given** capture input requiring private production data or privileged telemetry, **When** capture is requested, **Then** it produces no observed outcome and records the safety rejection or censor reason.

### Edge Cases

- A predeclared lane identifies more than one service, revision, workload, or outcome threshold.
- Execution evidence is successful but belongs to a different preparation, revision, runner identity, or lane definition.
- Deployment starts but its target identity, start time, or completion state cannot be verified.
- The observed threshold is met before the horizon but later evidence is missing, contradictory, or outside the frozen observation window.
- A rollback or replacement occurs during the window and breaks attribution to the deployed revision.
- Captured evidence has a content identity but cannot be read or its source is not within the predeclared release scope.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST require each lane to predeclare exactly one system, one service, one revision, one workload definition, one observation horizon, one outcome-threshold rule, one capture schema, and an allowed evidence/release scope before deployment or observation begins.
- **FR-002**: The system MUST accept a lane only when its supplied execution evidence is attributable to the predeclared revision and is eligible for replay under the prior build-qualification evidence. It MUST retain a censored result rather than substitute another revision when that condition is not met.
- **FR-003**: The system MUST create immutable lineage from the lane predeclaration through execution evidence, deployment evidence, and observation evidence. It MUST reject attribution based solely on timestamp proximity, textual similarity, shared authorship, or an asserted link.
- **FR-004**: The system MUST derive a deterministic lane identity from the frozen lane definition and referenced immutable upstream evidence. A change to any material lane input MUST yield a different identity or block capture.
- **FR-005**: The system MUST record deployment target identity, deployment lifecycle disposition, and attributable start and completion evidence before classifying an observation as observed.
- **FR-006**: The system MUST classify a lane only as `observed_positive`, `observed_negative`, or `censored`. It MUST use the frozen threshold rule and evidence wholly inside the frozen observation window for an observed class.
- **FR-007**: The system MUST classify a failed or ineligible build, deployment failure, unverifiable deployment, rollback or replacement that breaks attribution, incomplete observation window, invalid observation evidence, and monitoring gap as `censored` with an explicit reason. Censored evidence MUST NOT be reclassified as observed-negative.
- **FR-008**: The system MUST retain exactly one terminal capture record for every requested lane, including censored and blocked-before-observation attempts, with references or content identities for all retained evidence and explicit states for unavailable evidence.
- **FR-009**: The system MUST prohibit private third-party production data and privileged telemetry from becoming observation evidence. It MUST enforce the predeclared allowed evidence and release scope before retaining an observed outcome.
- **FR-010**: The system MUST preserve the score-time and observation times needed by the Stage 1 admission boundary and MUST not add post-window data to a captured outcome.
- **FR-011**: The system MUST label its output as replay-observation evidence only. It MUST NOT derive corpus admission, model performance, Semantic or Full Conformance, or automatic action from a capture result.

### Key Entities

- **ReplayLaneDefinition**: The frozen one-system, one-service, one-revision workload, horizon, outcome rule, capture schema, and allowed evidence scope.
- **DeploymentEvidence**: The attributable target, lifecycle disposition, timing evidence, and immutable linkage from an eligible execution to one deployed revision.
- **ObservationEvidence**: The bounded evidence collected within one frozen window, including its availability and content identity where retained.
- **ReplayCaptureRecord**: One terminal lane result containing its deterministic identity, full lineage, outcome class or censor reason, and claim boundary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In conformance tests, 100% of complete controlled lanes retain one lineage-complete record with exactly one observed outcome classification.
- **SC-002**: In conformance tests, 100% of controlled build/deployment failures, attribution breaks, incomplete windows, and monitoring gaps retain one censored record and no observed-negative classification.
- **SC-003**: In conformance tests, equivalent frozen lane inputs produce an identical lane identity, while every tested material input change produces a different identity or a blocked capture.
- **SC-004**: In conformance tests, 100% of inputs outside the allowed evidence scope produce no retained observed outcome.
- **SC-005**: Every retained capture record is auditable to its predeclaration and available upstream evidence without using a proximity-only link.

## Assumptions

- Feature 005 remains the authority for preparation, legal coverage, and build-qualification reduction; feature 006 remains the authority for execution containment and execution evidence.
- A later implementation supplies the approved replay deployment and telemetry boundaries. This feature defines their evidence contract and does not select an infrastructure provider, workload, horizon value, threshold, or telemetry product.
- One successful execution can only be associated with an observed outcome when the frozen lane definition and deployment attribution remain intact for the full observation window.

## Out of Scope

- Candidate discovery, source retrieval, legal research, build execution, or runner/container provisioning.
- Multi-service lanes, cross-system pooling, production-data acquisition, privileged telemetry collection, or mutable workload/threshold tuning.
- Corpus assembly or admission, model fitting/evaluation, conformance-class claims, publication, or automated remediation.

## Dependencies

- Feature 002 supplies the Stage 1 lineage, censoring, score-time, and single-system corpus-admission boundaries that this feature must preserve.
- Feature 005 supplies build preparation and qualification evidence.
- Feature 006 supplies immutable execution evidence for a prepared revision.
- Feature 008 may consume complete replay-capture evidence for corpus assembly; it does not alter this feature's capture or censoring decisions.
