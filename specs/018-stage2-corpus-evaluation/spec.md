# Feature Specification: Stage 2 Corpus Evaluation Gate

**Feature Branch**: `018-stage2-corpus-evaluation`

**Created**: 2026-09-08

**Status**: Draft

**Input**: User request to begin the stage after bounded replay-feasibility validation.

## Summary

Stage 2 feasibility established that one public replay lane can produce complete
records. This feature defines the next evidence gate: admit a predeclared,
replay-derived corpus for per-family evaluation without pooling incompatible
outcomes or upgrading a corpus result to Semantic Conformance by assertion.

## User Stories

### User Story 1 - Freeze corpus construction

As a researcher, I want corpus membership, revision selection, splits, outcome
definitions, censoring, and minimum label-yield thresholds frozen before
evaluation so that corpus adequacy cannot be tuned after scores are observed.

**Acceptance scenarios**

1. A corpus is accepted only when its predeclaration, replay-feasibility
   report, candidate revisions, structured outcome definitions, split policy,
   and release scope are hash-linked and ordered.
2. A corpus with duplicate revisions, cross-split leakage, post-score features,
   missing terminal records, or changed outcome definitions is rejected.
3. A corpus with only one observed outcome class is reported as inadequate for
   calibration/discrimination claims, even when replay coverage is complete.

### User Story 2 - Preserve family and censoring boundaries

As an evaluator, I want Change and Operational rows to retain shared-observation
lineage while remaining separately scoped so that per-family results cannot be
mistaken for pooled evidence.

**Acceptance scenarios**

1. Every admitted complete row has one shared observation identity and both
   family labels derived from the frozen definition.
2. Censored, blocked, withheld, and incomplete rows remain in denominators and
   cannot be relabeled as negatives.
3. A request to pool rows with different event or observation semantics is
   rejected before metric calculation.

### User Story 3 - Evaluate useful prediction, not calibration alone

As a reviewer, I want calibration and discrimination reported separately for
each family so a constant base-rate predictor cannot pass the evaluation gate.

**Acceptance scenarios**

1. Each family report includes calibration, discrimination, sample counts, and
   a non-degenerate score check.
2. A calibrated but constant predictor is rejected from the qualified result.
3. Metrics are withheld when label yield, split integrity, or minimum sample
   thresholds are not met.

### User Story 4 - Publish a bounded evaluation decision

As a reviewer, I want an independently verifiable report that distinguishes
corpus adequacy, per-family evaluation, and any future Semantic claim.

**Acceptance scenarios**

1. The report emits exactly one of `qualified`, `inconclusive`, or `blocked`.
2. `qualified` means only that the declared corpus/evaluation gates passed; it
   does not assert Semantic or Full Conformance by itself.
3. The report includes all withheld claims and the exact evidence needed for a
   later independent Semantic review.

## Functional Requirements

- **FR-001**: Represent an immutable corpus-evaluation profile containing the
  predeclaration, feasibility-report identity, corpus rows, family definitions,
  split policy, label-yield thresholds, score-time boundary, and release scope.
- **FR-002**: Require every corpus row to link to one selected revision and one
  validated Stage 2 terminal record.
- **FR-003**: Reject duplicate revisions, split leakage, mutable lane metadata,
  missing shared-observation lineage, and post-score prediction fields.
- **FR-004**: Preserve selected, terminal, complete, positive, negative,
  censored, blocked, withheld, and excluded denominators.
- **FR-005**: Reject pooled metrics unless the structured outcome definitions
  are directly commensurable or carry a valid recorded attestation.
- **FR-006**: Require both observed outcome classes and declared minimum sample
  sizes before qualified calibration or discrimination results are emitted.
- **FR-007**: Report calibration and discrimination independently for Change and
  Operational families, including score variance or an equivalent
  non-degeneracy check.
- **FR-008**: Ensure test/evaluation splits are time-ordered or explicitly
  justified and contain no revision or observation leakage.
- **FR-009**: Hash-link corpus rows, source revisions, replay evidence,
  prediction fields, metric inputs, and the final report without publishing
  private payloads.
- **FR-010**: Emit only `qualified`, `inconclusive`, or `blocked` and include a
  machine-readable reason for every failed or withheld gate.
- **FR-011**: Withhold Semantic, pooled cross-family, causal, generalization,
  and Full Conformance claims unless a separately approved claim gate consumes
  this report.

## Success Criteria

- **SC-001**: Every admitted revision has exactly one terminal record and every
  excluded revision has a recorded exclusion reason.
- **SC-002**: 100% of qualified rows have shared observation, window,
  threshold, and prediction-time lineage.
- **SC-003**: No constant-score predictor can receive a qualified family result.
- **SC-004**: Both families expose calibration, discrimination, counts, and
  withheld/blocked reasons independently.
- **SC-005**: An independent validator reproduces the report identity, counts,
  split checks, metric-input hashes, and claim boundary from released metadata.

## Out of Scope

- Acquiring a universal public corpus or selecting a production adapter.
- Publishing Semantic or Full Conformance.
- Pooling Change and Operational scores.
- Establishing causal validity, deployment realism, or generalization.
- Replacing the Stage 2 feasibility gate or the existing Stage 1 admission
  and per-family evaluation contracts.
