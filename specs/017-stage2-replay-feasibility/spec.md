# Feature Specification: Stage 2 Deterministic Replay Feasibility

**Feature Branch**: `017-stage2-replay-feasibility`

**Created**: 2026-09-07

**Status**: Draft

**Input**: User description: "Spec the next stage after Stage 1: define a bounded deterministic-replay feasibility stage that can establish whether a shared observation process is practical without overclaiming Semantic conformance."

## User Scenarios & Testing

### User Story 1 - Freeze a replay pilot before acquisition (Priority: P1)

As a researcher, I want to declare the replay lane, labels, thresholds, windows, sample, and analysis plan before collecting replay evidence so that the feasibility result cannot be tuned after observing outcomes.

**Why this priority**: A replay corpus is self-constructed. Without an ordered predeclaration and immutable lane definition, a successful pilot would not be auditable evidence for the Stage 2 route described by the authoritative Isoprax specification.

**Independent Test**: Given a screened public candidate and a complete predeclaration, the system accepts the pilot only when the declaration is cryptographically linked to an external anchor and is an ancestor of every corpus-data commit used by the pilot.

**Acceptance Scenarios**:

1. **Given** a candidate that passed replay selection, license, and prediction-time checks, **when** a pilot is prepared, **then** the system records the exact revisions, workload, observation horizon, outcome definitions, thresholds, censoring rules, split plan, and feasibility thresholds before acquisition begins.
2. **Given** a pilot artifact whose predeclaration is missing, mutable, or not an ancestor of its corpus-data commit, **when** the pilot is evaluated, **then** the result is blocked and no feasibility or semantic claim is emitted.
3. **Given** two definitions that have the same structured window, thresholds, and observation process but different prose, **when** the pilot is frozen, **then** their comparison key is equal; an attested equivalence is required when equality depends on a recorded named justification rather than direct structural equality.

### User Story 2 - Run a bounded replay lane with complete censoring (Priority: P1)

As a researcher, I want one replay lane to run through build, deployment, workload, and observation while retaining every failure and incomplete window so that feasibility is measured rather than inferred from survivors.

**Why this priority**: The main Stage 2 risk is operational feasibility at corpus scale. Dropping failed builds, deployment failures, or censored observation windows would inflate the apparent yield and undermine the evidence boundary.

**Independent Test**: Given a frozen lane and an injected replay backend, execute a bounded sample and verify that every selected revision has exactly one terminal record: complete observed-positive, complete observed-negative, censored, or blocked-before-compilation, with lineage to the immutable inputs.

**Acceptance Scenarios**:

1. **Given** a selected revision whose build, deployment, and observation window complete, **when** replay finishes, **then** the record contains both family labels derived from the same observation process, the prediction-time boundary, the shared window and thresholds, and evidence lineage.
2. **Given** a build, deployment, telemetry, workload, or infrastructure failure, **when** replay finishes, **then** the record preserves the failure stage and maps the revision to censored or blocked-before-compilation without treating it as a negative outcome.
3. **Given** a lane that changes its service, revision, workload, horizon, thresholds, schema, or evidence scope during execution, **when** the change is detected, **then** the lane is rejected as invalid rather than combining records under one lane identity.

### User Story 3 - Measure pilot feasibility and repeatability (Priority: P1)

As a researcher, I want a report that quantifies build and observation yield, throughput, resource estimates, and repeatability so that a full replay corpus can be accepted, revised, or stopped on explicit evidence.

**Why this priority**: Stage 2 should not proceed to an expensive corpus run without knowing whether the chosen candidate and replay environment can produce enough complete, legally releasable, semantically shared observations.

**Independent Test**: Given pilot terminal records and an optional repeated lane run, produce a deterministic feasibility report containing denominators, censoring, temporal coverage, throughput, resource/cost estimates, repeat-run discrepancies, and a status of `feasible`, `inconclusive`, or `blocked`.

**Acceptance Scenarios**:

1. **Given** a pilot with complete evidence for all required dimensions and thresholds met, **when** the report is generated, **then** it reports `feasible` for the declared pilot scope and identifies the assumptions used for any full-corpus extrapolation.
2. **Given** a pilot with insufficient positives, complete windows, build success, repeatability, or release evidence, **when** the report is generated, **then** it reports `inconclusive` and names the failed or underpowered dimension; it does not silently upgrade the result to feasible.
3. **Given** a missing license, private/privileged telemetry dependency, broken provenance, or invalid predeclaration ordering, **when** the report is generated, **then** it reports `blocked` and identifies the blocking evidence gap.
4. **Given** repeated execution of an identical lane, **when** terminal outcomes or labels disagree, **then** the report records the discrepancy and withholds a repeatability pass even if aggregate rates look acceptable.
5. **Given** a repeatability baseline, **when** a new thresholded pilot is
   declared, **then** its threshold is one resolved scalar derived from that
   baseline, with the derivation rule and baseline content hash recorded; no
   earlier observation is relabeled.
6. **Given** a thresholded feasibility pilot, **when** usable outcomes are
   reduced, **then** the report publishes a bounded positive/negative yield
   estimate and withholds corpus planning when either class is absent.

### User Story 4 - Publish a bounded evidence package (Priority: P2)

As a reviewer, I want to inspect the pilot inputs, outputs, exclusions, and limits without access to private infrastructure so that I can distinguish a replay-feasibility finding from a Semantic conformance claim.

**Why this priority**: Reproducibility and claim boundaries are part of the result. A useful Stage 2 artifact must show what was observed, what was censored, and what remains unproven.

**Independent Test**: Given a completed pilot, reconstruct its report from the released manifest and evidence files, verify hashes and counts, and confirm that no private or privileged telemetry is required to interpret the result.

**Acceptance Scenarios**:

1. **Given** a releasable pilot, **when** its evidence package is validated, **then** a reviewer can verify the predeclaration anchor, candidate/sample manifest, lane definition, terminal-record counts, exclusions, and report status.
2. **Given** a pilot that depends on unavailable private or privileged telemetry, **when** release validation runs, **then** the package is blocked or marked non-releasable and the dependency is explicit.
3. **Given** a feasible pilot, **when** its conclusion is rendered, **then** it states that the pilot establishes replay feasibility only; it does not assert pooled cross-family performance, Semantic conformance, or generalization to a full corpus.

### Edge Cases

- All selected revisions fail before compilation; the report must retain the blocked-before-compilation denominator and remain non-feasible.
- Builds succeed but no observation window completes; the report must distinguish zero event rate from zero usable observations.
- The pilot produces only positives or only negatives; calibration and discrimination are not declared established, and the report identifies the missing class.
- A threshold or window is changed after predeclaration; affected records are invalidated rather than relabeled.
- A replay environment cannot reproduce the declared dependency or workload; the lane is censored or blocked with the exact stage recorded.
- A repeated lane produces different telemetry or labels; the report preserves both runs and classifies the discrepancy instead of averaging it away.
- A candidate is publicly downloadable but its source, dataset, or telemetry terms do not permit the planned release; the pilot is blocked for release readiness.
- A pilot has enough complete records for throughput estimation but not enough for the declared label-yield or evaluation thresholds; feasibility is `inconclusive`, not `feasible`.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST represent a Stage 2 pilot as a frozen lane containing one public system/service, immutable revision set, workload, observation horizon, structured outcome definitions, thresholds, censoring rules, schema version, evidence scope, and declared feasibility thresholds.
- **FR-002**: The system MUST require a candidate to satisfy the existing replay-selection, license, prediction-time metadata, and predeclaration contracts before pilot execution.
- **FR-003**: The system MUST persist the predeclaration content hash, external timestamp or anchor, and ancestry proof showing that the predeclaration predates every corpus-data commit used by the pilot.
- **FR-004**: The system MUST use structured outcome-definition fields for comparison, including typed window duration and anchor, threshold tuples with metric/operator/value/sustain fields, and an observation-process identifier with parameters.
- **FR-005**: The system MUST support a recorded attested-equivalence path for differently represented definitions, including the attestor identity, justification, source artifacts, timestamp, and scope; attestation MUST NOT erase the original definitions.
- **FR-006**: The system MUST execute or delegate each lane stage through an auditable backend boundary covering source checkout, build, deployment, workload, and observation capture.
- **FR-007**: The system MUST retain exactly one terminal record per selected revision and classify it as complete observed-positive, complete observed-negative, censored, or blocked-before-compilation.
- **FR-008**: The system MUST derive both Change-family and Operational-family labels from the same observation process, shared threshold semantics, and shared window for a complete record; it MUST reject records that cannot establish that common lineage.
- **FR-009**: The system MUST preserve prediction-time information boundaries so that post-change observations cannot enter either family's prediction features.
- **FR-010**: The system MUST calculate pilot denominators and rates for commit selection, build completion, deployment completion, complete observation windows, positive/negative/censored outcomes, temporal coverage, and exclusions without removing failed or censored revisions from denominators.
- **FR-011**: The system MUST measure wall-clock throughput and resource or cost estimates for each replay stage and identify the assumptions and uncertainty used to extrapolate from the pilot to a proposed full corpus.
- **FR-012**: The system MUST support an explicitly declared repeated-lane check and report terminal-outcome, label, and evidence discrepancies without collapsing them into aggregate averages.
- **FR-013**: The system MUST validate that every released artifact is hash-linked to the lane, source revision, runner/environment identity, observation evidence, and report; private or privileged telemetry MUST be identified and cannot be silently treated as public evidence.
- **FR-014**: The system MUST emit exactly one pilot status from `feasible`, `inconclusive`, or `blocked`, with machine-readable reasons and supporting counts.
- **FR-015**: The system MUST withhold Semantic conformance, pooled cross-family metrics, and full-corpus adequacy claims from this feasibility feature; those claims require a separately specified and completed Stage 2 corpus/evaluation gate.
- **FR-016**: The system MUST provide deterministic validation of the evidence package so that an independent reader can recompute hashes, counts, lane identity, predeclaration ordering, and status from released artifacts.
- **FR-017**: A thresholded replay pilot MUST use a resolved scalar threshold
  derived only from a predeclared repeatability baseline; the baseline content
  hash and derivation description MUST be recorded separately from the
  machine-checked threshold value.
- **FR-018**: The feasibility reducer MUST estimate usable positive and
  negative outcome yield with bounded uncertainty and MUST report a
  non-estimable status when either class has zero observed yield.

### Key Entities

- **Replay Pilot Profile**: The predeclared, immutable description of a bounded Stage 2 lane, including candidate, sample, labels, thresholds, environment, workload, horizon, censoring, and feasibility gates.
- **Replay Lane**: One executable unit for a fixed system/service, revision, workload, observation process, and evidence scope.
- **Replay Terminal Record**: The immutable outcome for one selected revision, including stage status, labels when complete, censoring or blocking reason, and lineage.
- **Repeatability Check**: A comparison of repeated executions of the same lane inputs, preserving all discrepancies and their classification.
- **Feasibility Report**: A derived report containing denominators, yield, temporal coverage, throughput, resource estimates, repeatability, release readiness, status, and claim boundary.
- **Evidence Manifest**: The hash-linked inventory of predeclaration, source, runner, execution, observation, terminal-record, and report artifacts.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of pilot revisions have exactly one terminal record, including failed, censored, and blocked revisions; no terminal-record denominator is based only on successful survivors.
- **SC-002**: 100% of complete records used in the pilot report have verifiable shared observation-process, window, threshold, and prediction-time lineage for both family labels.
- **SC-003**: Before any pilot acquisition begins, the released evidence package verifies the predeclaration hash, external anchor, and ancestor relationship for 100% of corpus-data commits.
- **SC-004**: The feasibility report exposes counts and rates for every required build, deployment, observation, censoring, temporal-coverage, and release-readiness dimension, with no missing denominator represented as zero.
- **SC-005**: Any repeated-lane disagreement is preserved and causes the repeatability dimension to fail or remain inconclusive; no disagreement is hidden by aggregation.
- **SC-006**: An independent validation run reproduces the evidence-manifest hashes, terminal-record counts, lane identity, status, and claim boundary without private or privileged access.
- **SC-007**: Every pilot concludes with exactly one of `feasible`, `inconclusive`, or `blocked`; no pilot report produced by this feature claims Semantic conformance or pooled cross-family performance.
- **SC-008**: The report includes a declared full-corpus extrapolation with observed throughput, resource/cost range, censoring assumptions, and uncertainty; it may recommend proceeding, revising, or stopping but cannot substitute estimation for corpus evidence.
- **SC-009**: No thresholded pilot record can change outcome class without
  failing validation against the structured predeclared threshold.
- **SC-010**: A pilot with zero positive or zero negative usable events emits
  no finite implied corpus size and names the missing class.

## Assumptions

- Stage 0 and Stage 1 remain the current conformance baseline; Stage 1 real-data Structural validation does not become Semantic validation through this feature.
- Existing candidate-selection, build-qualification, hermetic-runner, observation-capture, and corpus-assembly contracts are reused and extended only where this feature explicitly requires a pilot-level integration or status.
- The first pilot uses one public project and one bounded lane; multi-project or multi-service corpus scale is a later decision informed by the feasibility report.
- The exact pilot sample size and full-corpus adequacy thresholds are declared in the predeclaration for the chosen candidate; this feature requires them to be explicit but does not invent a universal sample size.
- Backend execution remains injectable and implementation-neutral; this specification does not select a container runtime, cloud provider, telemetry stack, or build system.
- A complete replay record may support a future Semantic-validation dataset, but this feature alone does not authorize model training, pooled ranking, calibration claims, or publication of a Semantic result.
- Public release terms, source licenses, and telemetry terms are part of feasibility and may block a technically successful replay.

## Out of Scope

- Building or acquiring the full Stage 2 corpus.
- Declaring Semantic conformance or publishing pooled cross-family metrics.
- Choosing a production cloud, container platform, workload generator, telemetry vendor, or project-specific adapter.
- Replacing the existing Stage 1 structural-validation evidence or changing the authoritative Isoprax v0.3 outcome semantics.
- Inferring causal validity, deployment realism, or generalization from a pilot merely because its labels are commensurable.
