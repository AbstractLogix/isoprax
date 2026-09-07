# Feature Specification: Complete Stage 1 Public-Data Validation

**Feature Branch**: `016-stage1-public-validation`

**Created**: 2026-09-07

**Status**: Draft

**Input**: User description: "Fully finish Stage 1 using reproducible public Change and Operational data, frozen splits, per-family evaluation, and a publishable evidence report."

## Overview

Execute the existing Stage 1 admission and per-family evaluation contracts on
two bounded, licensed public sources: one ApacheJIT project for the Change
family and Google Cluster Trace v1 for the Operational family. Raw datasets
remain external; the repository stores the predeclaration, adapter, source
identities, hashes, and derived report. The feature does not pool families or
claim Semantic/Full Conformance.

## User Scenarios & Testing

### User Story 1 - Reproduce public source material (Priority: P1)

A reviewer can obtain the declared public files, verify their published
identity and local checksum, and rerun the adapter without private data or
network access in the core library.

**Independent Test**: Run the adapter against the two supplied source files
and compare source metadata, row counts, split boundaries, and report identity
with the checked-in evidence report.

**Acceptance Scenarios**:

1. **Given** the declared ApacheJIT and Google trace files, **when** the
   adapter runs, **then** it emits deterministic source hashes and derived
   counts.
2. **Given** a missing, changed, or malformed source file, **when** validation
   runs, **then** it fails closed and does not emit a successful report.

### User Story 2 - Validate each family under frozen Stage 1 gates (Priority: P1)

A reviewer can inspect independent Change and Operational reports showing
   lineage, score-time fields, chronological splits, calibration evidence,
   outcome counts, metrics, and uncertainty.

**Independent Test**: Run both source adapters and verify that admission gates
pass, rows remain single-system, and evaluation output identifies its family
and Outcome Definition.

**Acceptance Scenarios**:

1. **Given** Apache Ignite rows and Google job rows, **when** admission runs,
   **then** each family is evaluated separately with no cross-system pooling.
2. **Given** calibration-fit and calibration-gate rows, **when** evaluation
   runs, **then** the calibrator uses only the declared fit rows and the gate
   result is reported independently.
3. **Given** an uncalibrated or insufficient family result, **when** the report
   is generated, **then** it says so rather than promoting the result.

### User Story 3 - Publish bounded evidence (Priority: P1)

A reader can reproduce the reported evidence identity and understand exactly
what Stage 1 established and what remains outside scope.

**Independent Test**: Compare the checked-in JSON report with a fresh run and
inspect its claim boundary, source licenses, split metadata, counts, and
per-family statuses.

**Acceptance Scenarios**:

1. **Given** both reports, **when** a reader inspects the aggregate artifact,
   **then** it contains separate family results and no pooled metric.
2. **Given** the public-data artifact, **when** a reader asks whether it proves
   Semantic Conformance, **then** the report explicitly answers no.

## Requirements

- **FR-001**: The implementation MUST use only the declared public source
  artifacts and MUST record source URLs, versions/identifiers, licenses, and
  checksums.
- **FR-002**: The adapter MUST preserve one system boundary per evaluation and
  MUST reject cross-system pooling.
- **FR-003**: The adapter MUST derive score-time fields only from data available
  at the declared score time and MUST preserve fixed chronological splits.
- **FR-004**: The adapter MUST use the existing admission and per-family
  evaluation contracts rather than bypassing their gates.
- **FR-005**: Calibration MUST be fit only on `calibration_fit` rows and checked
  only on `calibration_gate` rows.
- **FR-006**: A failed calibration or incomplete evidence MUST remain
  `inconclusive` or `blocked`; it MUST NOT be relabeled as success.
- **FR-007**: The generated report MUST include source identity, predeclaration
  identity, split boundaries, per-split outcome counts, evaluation identity,
  calibration diagnostics, metrics, and explicit unavailable evidence.
- **FR-008**: The report MUST NOT contain a pooled cross-family metric or a
  Semantic/Full Conformance claim.
- **FR-009**: Fixed source bytes and fixed predeclaration MUST produce identical
  report identity and derived summaries.
- **FR-010**: Raw public datasets MUST remain outside the repository unless a
  future license review explicitly permits redistribution.

## Success Criteria

- **SC-001**: Both public source adapters pass source identity and provenance
  checks and produce deterministic reports.
- **SC-002**: Both family corpora pass Stage 1 admission, including lineage,
  score-time, split, censoring, and single-system gates.
- **SC-003**: Separate per-family evaluation results are produced, including an
  honest calibration status for each family.
- **SC-004**: A fresh run reproduces the checked-in report identity and counts.
- **SC-005**: The evidence remains explicitly below Semantic and Full
  Conformance, regardless of calibration outcomes.

## Out of Scope

- Cross-family pooled metrics or joint ranking.
- Semantic Conformance or predictive superiority claims.
- Private telemetry, production adapters, replay deployment, or model serving.
- Bundling the raw ApacheJIT or Google trace files in Git.

## Assumptions

- The declared source records remain available at their published URLs.
- The source licenses permit local analysis and redistribution of metadata and
  derived aggregate evidence, but not necessarily raw file redistribution.
- Stage 1 is complete as an executed, auditable structural validation even when
  a family honestly reports uncalibrated evidence.
