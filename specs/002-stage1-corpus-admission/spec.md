# Feature Specification: Stage 1 Corpus Admission and Replay Evidence

**Feature Branch**: `002-stage1-corpus-admission`
**Created**: 2026-09-05
**Status**: Ready for Planning
**Input**: Extend Isoprax beyond Stage 0 synthetic proof using a real paired corpus admission gate, reusing compatible archived decision records without importing JEPA/profile scope.

## Overview

Stage 0 proved structural contract mechanics offline with synthetic evidence.
Stage 1 defines how a real paired corpus is admitted for evaluation without
claim inflation or data leakage. This feature is evidence governance and corpus
admission plumbing, not model innovation.

## User Scenarios & Testing

### User Story 1 — Refuse inadmissible corpora (Priority: P1)

A reviewer submits a candidate corpus and receives a deterministic admission
result naming each failed gate.

**Acceptance Scenarios**:

1. **Given** incomplete observation windows, **When** admission runs,
   **Then** affected rows are censored and admission fails if gates are unmet.
2. **Given** prediction-time leakage fields, **When** admission runs,
   **Then** admission fails and names offending fields.
3. **Given** an adequate, lineage-complete corpus, **When** admission runs,
   **Then** admission succeeds and emits gate-by-gate evidence without assigning
   Semantic or Full conformance.

### User Story 2 — Audit row lineage end-to-end (Priority: P2)

A reviewer selects any admitted row and can trace it to source change,
deployment, and observation records with confidence classification.

**Acceptance Scenarios**:

1. **Given** an admitted row, **When** lineage is requested,
   **Then** change, deployment, and observation identifiers are returned.
2. **Given** ambiguous linkage confidence, **When** lineage is requested,
   **Then** confidence class and disposition are shown; ambiguity is never
   silently resolved.

### User Story 3 — Reproduce study design from manifests (Priority: P3)

An independent reader reconstructs split boundaries, horizon, and class counts
from published manifests.

**Acceptance Scenarios**:

1. **Given** published manifests only, **When** split boundaries are recomputed,
   **Then** boundaries match exactly.
2. **Given** published manifests only, **When** class totals are recomputed,
   **Then** observed-positive, observed-negative, and censored counts match.

## Edge Cases

- Observation window straddles a split boundary and follow-up cannot complete.
- Build or deployment failure produces no valid observation.
- Telemetry gaps occur inside `[T, T+H]`.
- Rollback occurs within the observation window.
- Multiple observations derived from one change (multi-workload replay) inflate
  apparent sample size unless clustered by change.
- Linkage candidates conflict and none exceed confidence threshold.
- A field appears plausible but is computed using history that extends beyond
  score time `T`.

## Requirements

### Functional Requirements

- **FR-001**: System MUST enforce immutable lineage from change → deployment →
  observation and reject linkage based only on proximity heuristics.
- **FR-002**: System MUST classify outcomes as observed-positive,
  observed-negative, or censored; censored rows MUST NOT be treated as
  negatives.
- **FR-003**: System MUST enforce prediction-time field allowlists and reject
  post-`T` information leakage.
- **FR-004**: System MUST enforce frozen chronological splits for training,
  calibration-fit, calibration-gate, and test periods.
- **FR-005**: System MUST enforce predeclared adequacy floors per split and
  fail admission with explicit deficits.
- **FR-006**: System MUST emit admission evidence reports that do not assign
  Semantic or Full conformance by themselves.
- **FR-007**: System MUST preserve Isoprax claim discipline: corpus admission is
  necessary evidence infrastructure, not a conformance-class upgrade.
- **FR-008**: System MUST classify each row as observed-positive,
  observed-negative, or censored and report these counts per split.
- **FR-009**: System MUST treat build failures, deployment failures,
  incomplete windows, and monitoring gaps as censored rows.
- **FR-010**: System MUST enforce full observation follow-up within each split
  or censor rows that cannot complete follow-up.
- **FR-011**: System MUST freeze split boundaries before fitting and MUST reject
  post-hoc split edits.
- **FR-012**: System MUST use four chronological non-overlapping periods:
  train, calibration-fit, calibration-gate, and test.
- **FR-013**: System MUST enforce calibration map fitting on calibration-fit and
  gate checks on calibration-gate only.
- **FR-014**: System MUST support manifest-first reproducibility with published
  split boundaries, horizon, and per-split class counts.
- **FR-015**: System MUST reject linkage established solely by timestamp
  proximity, textual similarity, or shared authorship.
- **FR-016**: System MUST require explicit prediction-time field allowlists and
  explicit forbidden-field lists for each admission profile.
- **FR-017**: System MUST fail admission if any prediction-time field is not
  known at score time `T`.
- **FR-018**: System MUST define a fixed horizon rule before outcomes are
  observed and MUST reject horizon tuning on post-outcome data.
- **FR-019**: System MUST preserve single-system corpus boundaries; cross-system
  pooling in one admitted corpus is forbidden.
- **FR-020**: System MUST emit deterministic, gate-by-gate pass/fail output with
  explicit failed-gate reasons.
- **FR-021**: System MUST never auto-promote admission success into Semantic or
  Full conformance status.
- **FR-022**: Where multiple observations derive from one change, system MUST
  cluster by change to avoid split leakage and account for within-change
  correlation in evaluation inputs.
- **FR-023**: Replay-derived artifacts MUST preserve project-independence rules:
  no third-party private production data or privileged telemetry.
- **FR-024**: System MUST record release scope metadata for each admitted
  corpus, including what artifacts are publishable.
- **FR-025**: Threshold definitions used to classify observed-positive outcomes
  MUST be frozen before corpus collection and not tuned on admitted outcomes.

### Key Entities

- **CorpusRow**: One change-linked observation row with lineage, score-time
  features, outcome class, and split assignment.
- **LineageChain**: Immutable identifiers for change, build/deployment, and
  observation sources.
- **OutcomeClass**: `observed_positive`, `observed_negative`, or `censored` plus
  censor reason.
- **SplitDefinition**: Frozen chronological boundaries and intended purpose.
- **AdmissionGateResult**: Deterministic pass/fail decision with evidence.
- **AdmissionManifest**: Publishable metadata for reproducibility and audit.

## Out of Scope

- JEPA or joint-latent profile implementation.
- New predictor families beyond existing Isoprax strategy contracts.
- Cross-system pooled corpora in one admission run.
- Real-world claim publication policy beyond admission evidence reporting.
- Final corpus acquisition operations and cloud provisioning (covered by later
  implementation features).

## Archive Reuse Boundaries

This feature may reuse archived decisions for:

- admission gate taxonomy,
- replay topology constraints,
- leakage/censoring discipline,
- manifest-first reproducibility.

This feature MUST NOT import archive-specific model/profile obligations by
inference.

## Success Criteria

- **SC-001**: Admission rejects any corpus violating lineage, censoring,
  leakage, split, or adequacy gates and reports failed gates deterministically.
- **SC-002**: Independent reproduction of split boundaries and per-split counts
  from manifests matches exactly.
- **SC-003**: Documentation and reports keep Stage 1 claims below Semantic/Full
  unless separate conformance evidence is produced.
- **SC-004**: Admission output is deterministic for identical inputs and stable
  across repeated runs.
- **SC-005**: Recomputed split and class statistics from published manifests
  match admitted-corpus reports exactly.

## Assumptions

- Candidate corpora and adapters are supplied in a later implementation feature.
- Stage 0 modules remain the contract and evaluation substrate for Stage 1.
- Any replay-specific horizon value remains externally justified and predeclared.

## Dependencies

- Existing Stage 0 contract modules in `isoprax/` remain authoritative for
  events/signals/commensurability semantics.
- Stage 1 adapters, capture pipelines, and candidate corpus manifests are
  delivered by follow-on implementation tasks.
- Implementation start requires an explicit project decision that this Stage 1
  extension is now in authorized Isoprax scope beyond the initial Stage 0
  synthetic reference boundary.
