# Feature Specification: Stage 1 Per-Family Evaluation

**Feature Branch**: `013-stage1-per-family-evaluation`  
**Status**: Draft

## Overview

Evaluate one admitted public corpus within one family using frozen splits,
predeclared metrics, calibration evidence, and uncertainty reporting. The
result is per-family evaluation evidence only; it does not pool families or
establish Semantic/Full Conformance.

## User Scenarios & Testing

### User Story 1 - Review frozen per-family results (Priority: P1)

A reviewer can reproduce predeclared, split-respecting metric and calibration
summaries from an admitted corpus.

**Acceptance Scenarios**:

1. Equivalent admitted inputs yield identical evaluation manifests and metrics.
2. Non-admitted, split-leaking, inadequate, or missing calibration evidence is
   rejected or reported inconclusive.
3. Every result identifies its family, outcome definition, uncertainty, and
   explicit non-pooling claim boundary.

## Requirements

- **FR-001**: Require a passing admission report, frozen profile, and one
  outcome definition/family per evaluation.
- **FR-002**: Enforce split isolation between fitting, calibration gating, and
  final evaluation.
- **FR-003**: Report predeclared metrics, calibration diagnostics, sample and
  censoring counts, uncertainty, and unavailable evidence explicitly.
- **FR-004**: Reject pooled cross-family metrics, post-hoc thresholds, missing
  predeclaration, and non-admitted corpora.
- **FR-005**: Fix the claim boundary below Semantic/Full Conformance and model
  efficacy beyond the observed, scoped evidence.

## Success Criteria

- **SC-001**: Deterministic fixtures reproduce all public summaries exactly.
- **SC-002**: All tested leakage and scope violations fail closed.

## Out of Scope

- Cross-family pooling, semantic claims, model training, online decisions, and
  automatic remediation.
