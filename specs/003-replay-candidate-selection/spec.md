# Feature Specification: Replay Candidate Selection and Predeclaration

**Feature Branch**: `003-replay-candidate-selection`

**Created**: 2026-09-05

**Status**: Draft

**Input**: User description: "Define how a candidate system is screened and how its analysis plan is predeclared and made tamper-evident, before any Stage 1 corpus (002) can be collected against it. Reuse compatible archived decision records without importing corpus-execution or JEPA/profile scope."

## Overview

This feature closes the missing evidence boundary between Stage 0 structural proof and Stage 1 corpus admission. It defines a deterministic candidate screen and a predeclared analysis-plan provenance record so later corpus admission checks can validate against a fixed plan rather than an after-the-fact narrative.

The implementation does not collect corpora or evaluate model quality; it only records the candidate screen, plan hash, ancestry, external anchor, and exclusion structure required by 002.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Screen a candidate deterministically (Priority: P1)

A reviewer submits a candidate system and receives a deterministic pass/fail result naming the first disqualifying screen, with every considered candidate outcome recorded.

**Independent Test**: Submit three synthetic candidates — one failing commit supply, one failing licence terms, one passing all screens — and verify each returns the correct disqualifying screen or a pass, with all three outcomes retained.

**Acceptance Scenarios**:

1. **Given** a candidate with commit supply below the adequacy floor implied by 002, **When** screening runs, **Then** the candidate is disqualified at Screen 1 and later screens are not evaluated.
2. **Given** a candidate whose licence forbids publication of benchmark measurements, **When** screening runs, **Then** the candidate is disqualified at Screen 2 regardless of commit supply.
3. **Given** a candidate passing Screens 1–2, **When** a sampled build-rate check is run, **Then** the candidate is disqualified if the success rate falls below the predeclared floor or failures cluster in time.
4. **Given** a candidate passing all four screens, **When** screening concludes, **Then** the candidate is marked eligible and the full screening record is retained.

---

### User Story 2 - Predeclare an analysis plan tamper-evidently (Priority: P1)

A reviewer writes an analysis plan for an eligible candidate, and the system produces evidence that the plan existed before any corpus-data commit was collected.

**Independent Test**: Write a predeclaration artifact, record its hash and commit, simulate a later edit, and verify admission-style rehashing detects the modification.

**Acceptance Scenarios**:

1. **Given** a predeclaration artifact, **When** its content hash is computed and later re-computed, **Then** an unmodified artifact matches and a modified artifact does not.
2. **Given** a predeclaration commit and later corpus-data commit, **When** ancestry is checked, **Then** the check executes an ancestry test and fails when the predeclaration commit is not an ancestor.
3. **Given** a predeclaration commit with no recorded external anchor, **When** the predeclaration is submitted for use, **Then** it is rejected as unanchored.
4. **Given** a soak-duration value in the predeclaration, **When** its derivation is checked, **Then** it is rejected if it was computed using any data from the observation window it bounds, and accepted if computed as a stated rule over training-period-only data.

---

### User Story 3 - Record exclusions structurally, not as deferrals (Priority: P2)

A reviewer consults the exclusion record to see which public datasets cannot support a Semantic claim and why before considering them as replay-avoidance shortcuts.

**Independent Test**: Query the exclusion record for a dataset with no code-change events and for a dataset with mismatched label processes; verify each returns a structural reason and neither is listed as pending.

**Acceptance Scenarios**:

1. **Given** a dataset containing no code-change events, **When** its exclusion entry is read, **Then** the reason states the structural absence of a Change-family event.
2. **Given** a dataset whose labels derive from different observation processes, **When** its exclusion entry is read, **Then** the reason cites Isoprax v0.3 §5.6 and states calibration does not change the conclusion.
3. **Given** the replay structural justification, **When** it is read, **Then** it is recorded as independent of paired-dataset scarcity and survives future large paired datasets unless that dataset also shares one observation process.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST screen candidates in a fixed order — commit supply, licence and publication terms, sampled historical build rate, and prediction-time metadata availability — and MUST NOT evaluate a later screen once an earlier one disqualifies a candidate.
- **FR-002**: System MUST record the screening outcome for every candidate considered, including disqualified candidates and their disqualifying screen.
- **FR-003**: System MUST disqualify a candidate at Screen 1 if projected commit supply cannot support the adequacy floor defined by 002 at the candidate's observed or estimated positive-event rate.
- **FR-004**: System MUST disqualify a candidate at Screen 2 if its licence forbids redistribution of derived metrics or publication of benchmark measurements.
- **FR-005**: System MUST disqualify a candidate at Screen 3 if a sampled build-attempt success rate falls below a predeclared floor or if build failures cluster in time such that dropping them would bias the corpus.
- **FR-006**: System MUST confirm, at Screen 4, that 002's prediction-time feature allowlist is populatable from the repository at each sampled commit before a candidate is marked eligible.
- **FR-007**: System MUST require a predeclaration artifact written before any corpus-data commit is collected, containing at minimum soak duration, derivation rule, positive-event definition and thresholds, censoring rule, drift and anchor thresholds, split boundaries, adequacy floor, and ablation comparison plan.
- **FR-008**: System MUST reject a soak-duration value computed using any data from the observation window it is meant to bound and MUST accept only a value derived as a stated rule over training-period-only data.
- **FR-009**: System MUST compute and record a content hash of the predeclaration artifact and MUST detect and reject a mismatch between the recorded hash and the artifact's current content when re-checked.
- **FR-010**: System MUST record the commit identifier containing the predeclaration artifact and execute an ancestry check confirming it is an ancestor of every corpus-data commit; a recorded claim of predeclaration order MUST NOT substitute for an executed check.
- **FR-011**: System MUST require at least one anchor for the predeclaration commit independent of the project's own repository and clock, recorded as an anchor type and retrievable reference, and reject a predeclaration with no such anchor.
- **FR-012**: System MUST require a public remote to be configured and the repository pushed to it before an anchor dependent on that remote is recorded.
- **FR-013**: System MUST reject any corpus-data commit whose timestamp precedes the anchored predeclaration commit from being treated as validly predeclared against.
- **FR-014**: System MUST maintain an exclusion record for datasets with no code-change events, stating the reason as the structural absence of a Change-family event and MUST NOT describe the dataset as pending or deferred.
- **FR-015**: System MUST maintain an exclusion record for datasets whose two families' labels derive from different observation processes, citing Isoprax v0.3 §5.6, stating calibration does not resolve the exclusion, and permitting continued use as Structural-conformance or baseline reference only.
- **FR-016**: System MUST record the structural replay justification as independent of paired-public-dataset scarcity and state that it survives future large paired datasets unless that dataset also shares one observation process across both families.

### Key Entities *(include if feature involves data)*

- **CandidateRecord**: One candidate system's identity, screening outcome per screen, and final eligibility disposition.
- **ScreeningResult**: The ordered per-screen pass/fail outcome for one candidate, including the disqualifying screen if failed.
- **PredeclarationArtifact**: The frozen analysis-plan document and its content hash.
- **ProvenanceRecord**: The predeclaration commit, ancestry-check result, hash, and external anchor.
- **ExclusionEntry**: A dataset's exclusion reason and residual use.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every candidate considered has a recorded screening outcome; the eligible candidate's record shows it passed all four screens in order.
- **SC-002**: A modified predeclaration artifact is detected by hash mismatch on 100% of tested modifications.
- **SC-003**: The ancestry check executes against real commit history and fails deterministically when a corpus-data commit predates the predeclaration commit.
- **SC-004**: No predeclaration lacking a recorded external anchor is accepted for use by a downstream admission run.
- **SC-005**: The exclusion record correctly classifies a fixed test set of no-code-change and mismatched-label-process datasets with no such entry describing itself as pending or deferred.

## Assumptions

- The candidate pool exists and is outside this feature's scope.
- The replay execution environment is a later implementation feature and is not required for screening or predeclaration.
- Git is the VCS in use for the predeclaration repository and the candidate repository.

## Out of Scope

- Selecting or announcing a specific candidate system.
- Running a pilot before FR-007 through FR-013 are satisfied.
- Designing or operating the replay execution environment.
- JEPA or joint-latent profile implementation.
- Corpus collection and admission proper.

## Archive Reuse Boundaries

This feature may reuse archived decisions for candidate-screening order, provenance mechanics, exclusion record entries, and soak-duration derivation rules. It must not import archive-specific replay-execution or JEPA/profile obligations by inference.

## Readiness Gate

This feature is ready when a screening record format exists and is exercised against at least one disqualifying and one passing synthetic candidate per screen; a predeclaration schema exists satisfying FR-007 and FR-008; and the hash/ancestry/anchor checks in FR-009–FR-012 are independently testable.
