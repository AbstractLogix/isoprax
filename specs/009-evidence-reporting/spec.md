# Feature Specification: Stage 1 Evidence Reporting

**Feature Branch**: `009-evidence-reporting`
**Status**: Ready for planning

## Overview

Provide a deterministic, publishable Stage 1 evidence report that reduces assembled corpus and admission evidence into a safe reader-facing summary. The report makes obtained evidence, missing evidence, censoring, provenance, and claim limits inspectable without exposing raw prediction fields, deployment payloads, observations, private data, or privileged telemetry. It is evidence publication infrastructure only: it cannot grant admission or any conformance class.

## User Scenarios & Testing

### User Story 1 - Publish a bounded evidence report (Priority: P1)

A release reviewer can generate a deterministic report from one assembled corpus and its admission evaluation, then independently identify the inputs, published artifacts, gate results, censoring, and explicit claim boundary.

**Independent Test**: Generate reports twice from equivalent inputs in a different order and verify identical report identities and safe content.

**Acceptance Scenarios**:

1. **Given** a complete assembled corpus, its frozen profile, and an admission evaluation, **When** the report is generated, **Then** it includes stable input identities, release scope, predeclaration evidence, published artifacts, runner/build evidence references, counts, censoring, provenance, and every admission gate result.
2. **Given** the same evidence in a different input order, **When** reports are generated, **Then** their identities and all ordered public summaries are identical.
3. **Given** a report, **When** a reader inspects it, **Then** no raw prediction values, deployment payload, observation payload, private data, or privileged telemetry is present.

### User Story 2 - Interpret incomplete evidence honestly (Priority: P1)

A release reviewer can tell whether the available evidence is admissible, blocked, or inconclusive without mistaking it for a Semantic or Full Conformance result.

**Independent Test**: Generate reports from failed admission gates, incomplete evidence, and censored corpus rows and verify explicit unavailable-evidence entries and a non-upgrading claim statement.

**Acceptance Scenarios**:

1. **Given** one or more failed admission gates, **When** the report is generated, **Then** it records every failed gate and reports the status as blocked or inconclusive, never as admitted.
2. **Given** a censored row or unavailable evidence, **When** the report is generated, **Then** it preserves the count and reason/category without fabricating a completed outcome.
3. **Given** passing admission gates, **When** the report is generated, **Then** it labels the result as admission evidence only and explicitly withholds Semantic and Full Conformance claims.

### User Story 3 - Reject unsafe publication inputs (Priority: P2)

A release workflow fails closed when provided contradictory, unverified, or out-of-scope material rather than publishing a misleading report.

**Independent Test**: Submit mismatched report inputs, non-public provenance, missing required artifact evidence, or unsupported claim scopes and verify a specific rejection.

**Acceptance Scenarios**:

1. **Given** assembly and admission records that do not describe the same frozen corpus/profile, **When** reporting is requested, **Then** generation is rejected.
2. **Given** private production data, privileged telemetry, or a release scope outside the assembled profile, **When** reporting is requested, **Then** generation is rejected.
3. **Given** missing predeclaration, artifact, provenance, runner, or completeness evidence, **When** reporting is requested, **Then** the report records that evidence as unavailable and cannot state a complete/admitted outcome unless the admission evaluation itself establishes it.

## Requirements

- **FR-001**: The system MUST produce a deterministic report identity and canonical public representation from an assembled corpus report and its corresponding admission evaluation.
- **FR-002**: The report MUST include assembly/profile identity, release scope, input identities/hashes, published artifacts, predeclaration anchor/hash, build and runner evidence references, provenance, freshness/completeness, outcome and censoring counts, unavailable-evidence entries, and all admission gate results.
- **FR-003**: The report MUST represent unavailable, incomplete, blocked, and censored evidence explicitly. It MUST NOT infer positive evidence or a completed outcome from absence of a record.
- **FR-004**: The report MUST use a deterministic status: `admission_evidence` only when the provided admission evaluation passed; otherwise `blocked` when a supplied gate failed, and `inconclusive` when required evidence is unavailable or incomplete.
- **FR-005**: The report MUST state an immutable claim boundary that admission, build qualification, corpus assembly, and replay observation evidence do not establish Semantic or Full Conformance, model efficacy, or cross-family score pooling.
- **FR-006**: The report MUST exclude raw prediction values, deployment and observation payloads, private production data, privileged telemetry, and any material outside the assembled profile's published release scope.
- **FR-007**: The system MUST reject mismatched assembly/admission identities, invalid or unsupported input claim scopes, incompatible release scopes, and provenance that permits private production data or privileged telemetry.
- **FR-008**: The system MUST expose report fields in stable order and only from validated source evidence, so a reviewer can reproduce the published summary without network access or hidden runtime state.

## Key Entities

- **Evidence report profile**: frozen publication context including expected release scope, predeclaration reference, provenance constraints, required evidence categories, and published artifacts.
- **Evidence report**: deterministic public summary of a corpus assembly, admission evaluation, evidence availability, safe references, status, and claim boundary.
- **Unavailable evidence entry**: a named expected evidence category with a reason that it is missing, incomplete, withheld, or outside scope.
- **Gate summary**: stable public representation of a Stage 1 admission gate's identifier, result, and message, excluding row-level raw material.

## Success Criteria

- **SC-001**: Equivalent valid inputs produce byte-for-byte equivalent canonical public reports and the same report identity in 100% of deterministic test runs.
- **SC-002**: 100% of generated reports expose the required claim boundary, admission gate summary, outcome/censoring counts, and unavailable-evidence section.
- **SC-003**: 100% of tested unsafe inputs (scope mismatch, non-public provenance, invalid claim scope, and assembly/admission mismatch) are rejected without returning a report.
- **SC-004**: A reviewer can classify each tested report as admission evidence, blocked, or inconclusive solely from its public content, with no case asserting Semantic or Full Conformance.

## Assumptions

- Feature 008 corpus assembly and Feature 002 admission evaluation remain the authoritative sources for rows, profiles, and gate decisions; this feature reduces rather than re-evaluates them.
- Evidence references may be published only as safe identifiers/hashes and metadata already allowed by the frozen release scope.
- A missing source record is reported as unavailable; the reporter does not access external services to fill gaps.

## Out of Scope

- Granting or changing corpus admission, Semantic/Full Conformance, model, efficacy, or cross-family pooling claims.
- Downloading, persisting, or exposing raw replay, prediction, deployment, observation, private, or privileged source data.
- Automated remediation, external publishing infrastructure, or real-data adapter implementation.
