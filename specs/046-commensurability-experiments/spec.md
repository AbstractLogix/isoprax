# Feature Specification: Commensurability Experiments and Evidence

**Feature Branch**: `codex/046-commensurability-experiments`

**Created**: 2026-10-05

**Status**: Converged

**Input**: User request to execute the approved IsoPrax experimental phase: correct the Feature 044 baseline audit, remove business-state assumptions from public boundaries, run Invalid-Aggregation Benchmark A and the shared-model experiment, compare operation-specific gating with simpler rules, keep the Haskell oracle bounded, and publish an evidence report.

## User Scenarios & Testing

### User Story 1 - Audit the public baseline and responsibilities (Priority: P1)

A reader can tell which Feature 044 work is part of the stated audit baseline and which later working-tree additions are outside it. Public boundary documents describe scientific and implementation responsibilities without assuming whether another project is private or public.

**Why this priority**: Experimental findings need a correct and implementation-neutral scope record.

**Independent Test**: Check the scope report against the baseline commit ancestry and tree. Search the public boundary pages for business-state assumptions.

**Acceptance Scenarios**:

1. **Given** the audit baseline descends from a Feature 044 merge, **when** a reader checks the audit, **then** the report assesses the tracked Feature 044 material and names any excluded later files precisely.
2. **Given** a reader checks a project boundary, **when** they read the Semadmit or Bouleusis responsibility, **then** it states runtime admission/verification enforcement or deliberation/epistemic-state ownership without a private/public business claim.

### User Story 2 - Reproduce Invalid-Aggregation Benchmark A (Priority: P1)

A researcher runs a deterministic synthetic benchmark with two locally calibrated lanes that forecast the same number for different events, observation processes, and windows, plus a valid same-target control.

**Why this priority**: The counterexample is the direct test of whether equal numeric values create a common event interpretation.

**Independent Test**: Run the documented command twice and compare the canonical outputs. Confirm lane metrics, pooled value, exact declared target and weights, permitted operations, and prohibited interpretations.

**Acceptance Scenarios**:

1. **Given** two synthetic lanes with constant forecast `0.80` and observed rate `0.80`, **when** their event definitions differ, **then** the runner reports local calibration and a numeric 50:50 mixture result while refusing to call it one common event probability.
2. **Given** the same records with one shared event definition, **when** the valid control runs, **then** the runner reports the explicitly named common-target pool.

### User Story 3 - Test shared model identity and gating alternatives (Priority: P1)

A researcher can inspect target-local results from one shared JEPA backend across different families, different horizons, and a same-target control. The researcher can compare operation-specific permissions with naive aggregation, one global commensurability label, and a metadata-only rule.

**Why this priority**: Shared model identity and operation-level precision are central hypotheses that must face executed controls.

**Independent Test**: Run the experiment and inspect target definitions, shared backend identity, sample/event counts, calibration, Brier score, AUC where defined, uncertainty, ranking, permission errors, interpretation errors, and decision changes.

**Acceptance Scenarios**:

1. **Given** one fitted JEPA backend emits scores for different outcome families and horizons, **when** the experiment runs, **then** it reports each target separately and computes no pooled metric for those targets.
2. **Given** a same-target control with predeclared 50:50 cohort weights, **when** pooling runs, **then** the output names the mixture estimand and weights before reporting pooled metrics.
3. **Given** the operation-gate challenge set, **when** the four rules are compared, **then** the output reports false permissions, unnecessary refusals, interpretation errors, rank changes, and decision changes under a named rule.

### User Story 4 - Read bounded evidence and next steps (Priority: P2)

A reader can distinguish established repository results, literature-supported statements, new synthetic findings, and remaining hypotheses in one linked report.

**Why this priority**: The experimental output is useful only if its evidence strength and limitations stay clear.

**Independent Test**: Answer all five requested evidence questions from the report, follow its commands and source links, and confirm the Haskell oracle remains an independent public-semantics check.

**Acceptance Scenarios**:

1. **Given** an experimental result, **when** it is described, **then** the report labels it synthetic and does not claim production efficacy or Semantic/Full Conformance.
2. **Given** the Haskell oracle, **when** the report describes its role, **then** it remains bounded to public semantics and is not expanded into a general trust engine.

### Edge Cases

- A pooled numeric statistic is only emitted with an exact target or mixture estimand and predeclared weights.
- Different event families and different horizons remain separate even when backend identities and numeric scores match.
- A target with one outcome class has no meaningful ROC AUC; the report marks it unavailable.
- A shared source or dependent evidence pair does not become independent because model identifiers differ.
- Bootstrap resamples without both classes do not contribute an AUC interval; the output records the method and usable resample count.
- Synthetic sample sizes and calibrated scores do not establish real-world performance or conformance.

## Requirements

### Functional Requirements

- **FR-001**: The scope audit MUST reconcile the baseline commit's ancestry with the Feature 044 statement and assess tracked baseline material.
- **FR-002**: Any intentionally excluded Feature 044 work MUST be identified by exact path/state and reason.
- **FR-003**: The Semadmit and Bouleusis public boundaries MUST describe implementation-neutral responsibilities, including runtime admission/verification enforcement and deliberation/epistemic-state behavior.
- **FR-004**: Benchmark A MUST generate deterministic synthetic rows for two locally calibrated lanes with equal numeric forecasts and different event, observation-process, and window definitions, plus a valid same-target control.
- **FR-005**: Benchmark A MUST report lane metrics, pooled numeric values, the exact estimand and weights for every pool, permitted operations, and prohibited or unsupported interpretations.
- **FR-006**: The shared-model experiment MUST use the existing JEPA reference with one shared backend identity for different-family, different-horizon, and same-target cases.
- **FR-007**: The shared-model report MUST provide per-target calibration, Brier score, discrimination where meaningful, sample and event counts, event rate, uncertainty, and ranking behavior.
- **FR-008**: The shared-model experiment MUST emit pooled metrics only for a predeclared mixture estimand with predeclared weights.
- **FR-009**: The operation-gate comparison MUST include naive aggregation, one global label, a metadata-only rule, and operation-specific gating, with false permission, unnecessary refusal, interpretation, ranking, and decision measures.
- **FR-010**: The evidence report MUST answer the five user questions and distinguish repository results, primary literature, new experimental findings, and remaining hypotheses.
- **FR-011**: The Haskell oracle MUST remain an independent differential check of public IsoPrax semantics and MUST NOT grow into a general trust/admission engine.
- **FR-012**: All new experiment claims MUST be labeled synthetic and MUST NOT claim production efficacy or Semantic/Full Conformance.
- **FR-013**: The runner MUST use deterministic seeds and produce reproducible machine-readable output without adding runtime dependencies.

### Success Criteria

- **SC-001**: The baseline note agrees with `38cfc27` ancestry and names the later uncommitted Feature 044 paths excluded from that tracked baseline.
- **SC-002**: Two consecutive runner executions produce byte-identical canonical JSON output.
- **SC-003**: Benchmark A reports 100 records in each lane, forecast mean `0.80`, event rate `0.80`, and Brier score `0.16` per lane, with the invalid common-event interpretation withheld.
- **SC-004**: Different-family and different-horizon JEPA outputs share one backend identity, stay unpooled, and include all required target-local measures.
- **SC-005**: The same-target positive control reports a 50:50 declared mixture target before its pooled metrics.
- **SC-006**: The gate comparison reports all required errors and decision/ranking changes for the fixed challenge set, with the challenge-set limitation stated.
- **SC-007**: The report answers all five requested questions and labels repository, literature, synthetic findings, and open hypotheses separately.
- **SC-008**: Focused experiment and conformance tests pass; no Haskell trust-engine expansion is present.

## Assumptions

- The output is a deterministic synthetic research artifact, not a real-world efficacy study.
- The existing CPU JEPA reference backend is sufficient; the optional GPU backend is not required.
- `38cfc27` is the audit baseline named by Feature 045. Later uncommitted GADFPD/RCAEval qualification work remains outside that historical tree.
- The gate challenge set measures behavior on declared synthetic cases. It cannot estimate real-world error rates or settle operation-specific commensurability in general.
- Existing literature sources in the repository remain the literature set for this bounded report; new technical claims require primary-source support.
