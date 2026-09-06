# Feature Specification: Hermetic Runner Integration

**Feature Branch**: `006-hermetic-runner-integration`
**Created**: 2026-09-06
**Status**: Ready for planning

## Overview

This feature connects the approved build recipe from feature 005 to one explicitly configured local or container runner. For every eligible revision, a reviewer can create immutable execution evidence while preserving the frozen sample, recipe, runner image identity, non-root execution, read-only source input, and isolated writable work area. It produces execution evidence only; it neither qualifies a candidate by itself nor establishes any Isoprax conformance class.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execute an approved recipe safely (Priority: P1)

A reviewer submits a prepared build sample with an approved runner configuration and receives one terminal result for every selected revision.

**Why this priority**: The measured build evidence deferred by feature 005 is not meaningful unless the actual executor preserves its predeclared safety and reproducibility conditions.

**Independent Test**: A deterministic local runner fixture receives an immutable-image configuration, read-only source input, isolated writable work area, non-root identity, and frozen recipe. It executes only the approved command and records the effective execution settings. Unsafe configurations make zero compilation invocations.

**Acceptance Scenarios**:

1. **Given** a prepared, eligible revision and a complete approved runner configuration, **When** execution begins, **Then** it uses the frozen recipe and immutable runner identity without changing either input.
2. **Given** a runner identity without a digest, a root execution identity, a writable source input, or no isolated writable work area, **When** execution is requested, **Then** the revision is `blocked-before-compilation` and no build command starts.
3. **Given** a configured network-disabled execution environment, **When** a recipe attempts to obtain a mutable dependency, **Then** the attempt cannot alter the frozen recipe or make the result appear successful.

### User Story 2 - Preserve complete, attributable execution evidence (Priority: P1)

A reviewer can inspect the material facts of every execution and associate them with exactly one prepared revision.

**Why this priority**: A build exit code alone cannot establish what was run or whether the stated containment controls were in effect.

**Independent Test**: Controlled success, build-failure, timeout, infrastructure-unavailable, and artifact-producing fixture runs retain one evidence record per revision with the correct classification and stable references.

**Acceptance Scenarios**:

1. **Given** a successful execution, **When** it finishes, **Then** its record includes the preparation hash, revision, runner digest, frozen command, effective limits, terminal exit disposition, timestamps or elapsed duration, and references to retained output artifacts.
2. **Given** a build-process failure, timeout, or interruption after the build command starts, **When** the run terminates, **Then** it is retained as `censored` with its observed disposition; it is not dropped or converted to success.
3. **Given** unavailable runner infrastructure or a failed containment preflight, **When** execution cannot safely begin, **Then** it is retained as `blocked-before-compilation` with a reason.
4. **Given** an output artifact, **When** evidence is retained, **Then** its content identity and collection status are recorded; missing or unreadable artifacts are explicit rather than silently omitted.

### User Story 3 - Reproduce and audit an execution attempt (Priority: P2)

A reviewer can independently determine whether two records describe the same authorized attempt and whether either execution deviated from its frozen inputs.

**Independent Test**: Equivalent fixture runs produce the same execution identity; changing a revision, runner digest, command, limit, or source/input mount disposition changes that identity or blocks execution before compilation.

**Acceptance Scenarios**:

1. **Given** equivalent frozen inputs and an equivalent effective runner configuration, **When** execution identities are derived, **Then** they are identical.
2. **Given** any changed frozen input or effective containment control, **When** an execution identity is derived, **Then** it differs from the original or the execution is blocked before compilation.

## Edge Cases

- The runner process cannot be created, exits before the build command starts, or loses its output channel.
- The configured timeout or resource limit cannot be applied or verified.
- A recipe exits successfully but a required declared artifact is absent.
- The source path is unavailable, contains a revision other than the prepared revision, or cannot be mounted read-only.
- An execution record conflicts with the preparation hash, revision, or immutable runner identity supplied by feature 005.
- Artifact collection fails after a terminal process outcome is known.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept execution only for a non-blocked `BuildPreparation` from feature 005 and MUST preserve its preparation hash, selected revision, recipe reference, and runner identity in the execution record.
- **FR-002**: The system MUST require a digest-pinned runner image or other immutable runner identity, a non-root execution identity, read-only source input, and an isolated writable work area before starting a build command.
- **FR-003**: The system MUST require the command, timeout, resource limits, network policy, declared output paths, and runner configuration to be predeclared. It MUST block execution if any required control is absent, mutable, or cannot be applied.
- **FR-004**: The system MUST execute only the frozen recipe for the prepared revision. It MUST NOT rewrite the recipe, fetch mutable dependencies, or permit the execution to modify the source input.
- **FR-005**: The system MUST create one immutable execution-evidence record per execution attempt containing the preparation hash, revision, effective runner identity and controls, command identity, terminal disposition, and retained-output references.
- **FR-006**: The system MUST content-identify every collected declared output artifact and explicitly record each artifact that is absent, unreadable, or not collected.
- **FR-007**: The system MUST classify an unavailable runner, unavailable source input, or failed preflight as `blocked-before-compilation`. It MUST classify a build-process failure, timeout, or interruption after command start as `censored`.
- **FR-008**: The system MUST derive a deterministic execution identity from the frozen preparation and effective runner controls. A changed revision, runner identity, command, limit, network policy, or mount disposition MUST change that identity.
- **FR-009**: The system MUST preserve the complete result set and MUST NOT derive build rate, candidate qualification, corpus admission, or an Isoprax conformance claim from this feature's output alone.

### Key Entities

- **ApprovedRunnerConfiguration**: predeclared immutable runner identity, command, limits, network policy, source/work mounts, and declared outputs.
- **EffectiveRunnerControls**: the verified controls applied to one execution attempt.
- **ExecutionEvidenceRecord**: immutable per-attempt linkage to a prepared revision, terminal disposition, effective controls, and output evidence.
- **ArtifactEvidence**: a declared output's path, collection state, and content identity when collected.

## Success Criteria *(mandatory)*

- **SC-001**: 100% of executions with a missing or unverifiable required containment control are blocked before a build command starts in conformance tests.
- **SC-002**: 100% of terminal execution attempts retain exactly one evidence record linked to the prepared revision and preparation hash in conformance tests.
- **SC-003**: 100% of controlled post-start failures, timeouts, and interruptions are retained as censored results in conformance tests.
- **SC-004**: Equivalent frozen inputs yield identical execution identities, while each tested material control change yields a different identity or a blocked result.
- **SC-005**: No test path from this feature emits a build qualification, corpus-admission decision, or Isoprax conformance-class upgrade.

## Assumptions

- Feature 005 remains the authority for prepared-sample validation, legal coverage, per-row result reduction, and build qualification.
- The integrating environment supplies an approved runner implementation and enough local storage to retain the declared evidence. This feature does not select a container engine, registry, image, candidate, or resource-limit values.
- Where a runner cannot provide a required control, it is unsuitable for this feature and execution is blocked rather than emulated or weakened.

## Out of Scope

- Candidate discovery, source retrieval, legal research, or mutable dependency acquisition.
- Workload or deployment execution, operational telemetry, outcome observation, corpus assembly, model evaluation, or conformance claims.
- Defining a production container platform, provisioning runner infrastructure, or publishing artifact storage outside the explicitly retained evidence.

## Dependencies

- Feature 005 supplies the prepared-sample and injected-runner contract.
- Feature 007 may consume retained execution evidence for observation capture; it is not implemented here.
