# Feature Specification: Replay Corpus Assembly

**Feature Branch**: `008-corpus-assembly`
**Status**: Draft

## Overview

Transform frozen replay observations into a single-system corpus and manifest suitable for the existing 002 admission gate. This feature assembles evidence; 002 remains the authority that accepts or rejects it.

## User Scenarios & Testing

### User Story 1 - Assemble an auditable corpus (Priority: P1)

A reviewer receives one row per replayed change with score-time fields, outcome class, split, and complete lineage.

**Acceptance Scenarios**:

1. **Given** complete observation evidence, **When** assembly runs, **Then** rows preserve score-time metadata and frozen chronological splits.
2. **Given** censored lane evidence, **When** assembly runs, **Then** it remains censored and is never converted to a negative.

## Requirements

- **FR-001**: MUST create only 002-compatible single-system corpus rows and manifests.
- **FR-002**: MUST preserve lineage, censoring, score-time allowlists, and frozen splits.
- **FR-003**: MUST reject unknown-at-score-time fields and mutable threshold/split inputs.
- **FR-004**: MUST retain change clustering information for downstream evaluation.

## Success Criteria

- **SC-001**: Every assembled row is traceable to captured replay evidence or has an explicit rejection reason.

## Out of Scope

- Admission decisions, model training, or Semantic/Full claims.
