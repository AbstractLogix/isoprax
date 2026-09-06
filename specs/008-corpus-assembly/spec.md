# Feature Specification: Replay Corpus Assembly

**Feature Branch**: 008-corpus-assembly
**Created**: 2026-09-06
**Status**: Ready for planning
**Input**: User description: "start the next spec after replay observation capture"

## Overview

This feature transforms frozen replay-capture evidence from one system into deterministic candidate corpus rows and a reproducibility manifest for the existing Stage 1 admission gate. It preserves each captured outcome or explicit censoring, score-time boundaries, change clustering, and release scope. It assembles evidence only: feature 002 remains the authority for admission, and no model or conformance claim is produced.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Assemble an auditable candidate corpus (Priority: P1)

A reviewer supplies compatible captured lanes and one frozen assembly profile, then receives one deterministic candidate row per accepted replayed change with full lineage and an assembly report.

**Why this priority**: Stage 1 evaluation cannot begin safely until replay evidence can be transformed into reviewable, single-system rows without losing lineage or changing outcomes.

**Independent Test**: Equivalent complete capture records and an unchanged profile produce the same ordered rows, identifiers, lineage, score-time metadata, outcome classes, change groups, and manifest inputs.

**Acceptance Scenarios**:

1. **Given** compatible captured lanes from one system and a frozen assembly profile, **When** assembly runs, **Then** every accepted lane produces one row linked to its capture, deployment, and observation evidence.
2. **Given** a complete observed capture and a censored capture, **When** assembly runs, **Then** their outcome classes are preserved exactly and the censored capture is never converted into an observed negative.
3. **Given** equivalent input evidence in a different order, **When** assembly runs, **Then** the rows, report, and manifest inputs have the same deterministic order and identities.

---

### User Story 2 - Refuse unsafe or inconsistent inputs (Priority: P1)

A reviewer receives explicit rejections instead of a silently altered corpus when a lane violates the frozen single-system, split, score-time, threshold, or lineage contract.

**Why this priority**: An apparently usable corpus with mutable or post-outcome inputs would invalidate later admission and evaluation.

**Independent Test**: Inputs with a foreign system, duplicate change, incomplete lineage, unknown or post-score-time field, changed horizon or threshold, mutable split definition, or impossible follow-up receive an explicit rejection and do not appear in candidate rows.

**Acceptance Scenarios**:

1. **Given** input from more than one system, **When** assembly runs, **Then** foreign-system lanes are rejected and the report names each rejection.
2. **Given** an unallowed field or a field observed after its row score time, **When** assembly runs, **Then** the affected lane is rejected before it can enter the corpus.
3. **Given** a score time or complete observation window outside the frozen chronological split, **When** assembly runs, **Then** the affected lane is rejected with its split or follow-up reason.

---

### User Story 3 - Publish bounded assembly evidence (Priority: P2)

A reviewer can inspect a deterministic manifest and rejection report sufficient for later admission review without exposing raw restricted inputs or asserting admission.

**Why this priority**: Corpus assembly is only credible when the reader can reproduce its design and distinguish accepted evidence from rejected or unavailable evidence.

**Independent Test**: A successful assembly exposes its profile identity, source system, frozen horizon/threshold/splits, allowed release scope, row/rejection counts, and publishable artifact references; an incomplete assembly remains explicitly non-admitted.

**Acceptance Scenarios**:

1. **Given** an assembled candidate corpus, **When** a reviewer reads its manifest, **Then** they can reproduce its frozen profile and class counts without raw restricted telemetry.
2. **Given** any rejected capture or an empty accepted set, **When** an assembly report is produced, **Then** it preserves explicit rejection reasons and makes no admission, performance, or conformance claim.

### Edge Cases

- Two captures describe the same change but conflict in deployment, outcome, or score time.
- A capture record has the evidence-only claim scope but a missing deployment or observation identifier.
- A predeclared split definition overlaps another split, changes after profile freeze, or leaves no room for full observation follow-up.
- A censored capture has unavailable observation evidence, while an observed capture has a missing publishable artifact reference.
- A field is allowed by name but has no score-time observation timestamp.
- The assembly profile's release scope would publish private production data or privileged telemetry.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST require a frozen assembly profile before accepting captures. The profile MUST declare exactly one expected system, immutable chronological splits, allowed and forbidden prediction fields, a frozen horizon rule, a frozen threshold identifier, an allowed release scope, and publishable artifact references.
- **FR-002**: The system MUST accept only replay-capture records labeled as replay-observation evidence and create at most one candidate row per change within one assembly. It MUST retain an explicit rejection when required capture lineage, deployment identity, observation identity, or change identity is unavailable or conflicting.
- **FR-003**: The system MUST preserve each accepted capture's outcome class and censor reason exactly. Censored evidence MUST NOT become observed-negative, and an observed class MUST NOT be synthesized from missing capture evidence.
- **FR-004**: The system MUST preserve immutable linkage from a candidate row to its replay capture, execution, deployment, and observation evidence. It MUST reject linkage based solely on timestamp proximity, textual similarity, shared authorship, or an asserted link.
- **FR-005**: The system MUST assign each accepted row to exactly one predeclared chronological split using its score time and MUST reject observed outcomes without complete follow-up inside that split.
- **FR-006**: The system MUST permit only predeclared prediction fields with a recorded observation time at or before the row score time. It MUST reject forbidden, unknown, missing-timestamp, or post-score-time fields.
- **FR-007**: The system MUST reject captures whose system, horizon rule, threshold identifier, release scope, or score/observation window differs from the frozen assembly profile.
- **FR-008**: The system MUST record the source change as the row change group and preserve that group for downstream split-leakage and correlation controls.
- **FR-009**: The system MUST deterministically order accepted rows and rejected inputs and derive stable identities from the frozen profile and retained evidence.
- **FR-010**: The system MUST emit an assembly report and a manifest-input record that identify the profile, accepted rows, class counts, rejected inputs, release scope, and unavailable evidence without embedding raw restricted inputs.
- **FR-011**: The system MUST label every output as corpus-assembly evidence only. It MUST NOT make an admission decision, model-performance claim, Semantic or Full Conformance claim, or automatic action.

### Key Entities

- **CorpusAssemblyProfile**: Frozen one-system split, field, horizon, threshold, release-scope, and publication rules.
- **ReplayCaptureInput**: One capture record plus its score-time prediction fields and field observation times.
- **CandidateCorpusRow**: One accepted change-grouped row with complete evidence lineage, outcome/censor state, score-time fields, and frozen split.
- **AssemblyRejection**: One rejected input identity, requirement reason, and safe diagnostic reference.
- **CorpusAssemblyReport**: Deterministic accepted/rejected result, class counts, profile identity, manifest input, and evidence-only claim boundary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In conformance tests, 100% of compatible one-system capture inputs yield exactly one lineage-complete candidate row per accepted change.
- **SC-002**: In conformance tests, 100% of censored captures remain censored and 100% of invalid inputs are absent from accepted rows with an explicit rejection.
- **SC-003**: In conformance tests, equivalent profile and capture inputs produce identical row ordering, identities, class counts, and manifest input.
- **SC-004**: In conformance tests, 100% of foreign-system, duplicate-change, split/follow-up, profile-mismatch, forbidden-field, unknown-field, missing-time, and post-score-time cases are rejected.
- **SC-005**: Every assembly report states its evidence-only claim boundary and identifies retained versus unavailable publishable evidence.

## Assumptions

- Feature 007 supplies immutable capture records but does not itself select prediction fields or chronological splits.
- Feature 002 remains the normative authority for Stage 1 admission; this feature prepares compatible inputs and does not duplicate its final gate decision.
- A later caller supplies predeclared profile values and safe score-time prediction fields. The reference implementation does not retrieve production data, discover fields, or infer split/horizon/threshold values.

## Out of Scope

- Replay deployment, observation capture, source retrieval, legal research, or telemetry acquisition.
- Selecting a candidate system, prediction features, split boundaries, threshold values, release policy, or real-world dataset.
- Admission decisions, calibration/model fitting, evaluation, publication of raw restricted inputs, conformance upgrades, or automated remediation.

## Dependencies

- Feature 002 supplies Stage 1 admission vocabulary and its lineage, censoring, score-time, split, single-system, clustering, and claim boundaries.
- Feature 007 supplies replay-capture evidence that this feature can transform without changing its outcomes.
- Feature 009 may publish bounded assembly/admission evidence; it does not change assembly or admission decisions.
