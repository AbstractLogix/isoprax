# Feature Specification: Stage 1 Per-Family Evaluation

**Feature Branch**: `013-stage1-per-family-evaluation`
**Created**: 2026-09-06
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

1. **Given** equivalent admitted inputs, **When** evaluation runs, **Then** it
  produces identical evaluation manifests and metric summaries.
2. **Given** non-admitted inputs, split leakage, or missing/inadequate
  calibration evidence, **When** evaluation runs, **Then** it is rejected or
  reported as inconclusive.
3. **Given** any produced result, **When** it is published, **Then** it
  identifies its family, outcome definition, uncertainty, and an explicit
  non-pooling claim boundary.

## Requirements

- **FR-001**: Require a passing admission report, frozen profile, and one
  outcome definition/family per evaluation.
- **FR-002**: Enforce split isolation between fitting, calibration gating, and
  final evaluation.
- **FR-003**: Report predeclared metrics, calibration diagnostics, sample and
  censoring counts, uncertainty, and unavailable evidence explicitly.
- **FR-004**: Reject pooled cross-family metrics, post-hoc thresholds, missing
  predeclaration, and non-admitted corpora.
- **FR-005**: Fix the claim boundary below Semantic/Full Conformance and
  prohibit model-efficacy claims beyond the observed, scoped evidence.

## Success Criteria

- **SC-001**: Deterministic fixtures reproduce all public summaries exactly.
- **SC-002**: All tested leakage and scope violations fail closed.

## Out of Scope

- Cross-family pooling, semantic claims, model training, online decisions, and
  automatic remediation.
