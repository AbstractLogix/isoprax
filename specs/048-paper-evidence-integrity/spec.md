# Feature Specification: Research Paper Evidence Integrity

**Feature Branch**: `codex/047-retrieval-selection-benchmark`

**Created**: 2026-10-09

**Status**: Draft

**Input**: User request to audit and revise the IsoPrax research paper, separate paper scopes, independently recompute claims from raw artifacts, add falsification cases, and prepare a reproducible reviewer package.

## User Scenarios & Testing

### User Story 1 - Trace a paper claim to its evidence (Priority: P1)

A reader can identify whether a claim is a definition, a repository result, a synthetic finding, a literature-supported statement, or an open hypothesis. The reader can locate the source, protocol, result, uncertainty, and known limit for each claim.

**Why this priority**: The paper must not imply evidence that the repository or literature does not provide.

**Independent Test**: Validate each manuscript claim ID against the registry and source artifact hashes.

**Acceptance Scenarios**:

1. **Given** a numeric claim in the paper, **when** the integrity command runs, **then** it finds a reproducible result and matching source evidence.
2. **Given** a claim without reproducible raw evidence, **when** the registry is reviewed, **then** it is labeled unavailable or excluded from the paper's supported conclusions.

### User Story 2 - Recompute frozen results (Priority: P1)

A reader can verify raw artifact integrity and recompute the reported results without model calls or changes to frozen prompts, cases, labels, or analysis choices.

**Why this priority**: Reports and aggregate tables are not substitutes for the underlying records.

**Independent Test**: Run the replication command from the locked project environment and compare generated metrics with the registered claim results.

**Acceptance Scenarios**:

1. **Given** unmodified raw artifacts, **when** the replication command runs, **then** it verifies hashes, run structure, raw counts, and registered metrics.
2. **Given** a changed artifact or an unsupported numeric claim, **when** the command runs, **then** it fails with the artifact or claim ID.

### User Story 3 - Assess scope and submission readiness (Priority: P2)

An author or reviewer can see which evidence belongs to the cross-family contract paper, which belongs to a separate model-role study, and which limits prevent submission or independent-validation claims.

**Why this priority**: The synthetic model-role study does not establish JIT/AIOps semantic equivalence.

**Independent Test**: Review the scope decision, revised manuscript, companion outline, and reviewer packet against the registry.

**Acceptance Scenarios**:

1. **Given** the scope decision, **when** a result is assigned to a paper, **then** it directly supports that paper's stated question or is explicitly excluded.
2. **Given** no external scientific review, **when** readiness is reported, **then** automated checks are not described as independent scientific validation.

## Edge Cases

- A raw record can be available only in a pinned, private supporting repository; the package must identify the exact source and say whether an independent reader can access it.
- Two raw runs can be byte-identical while still using one fixed case set; this supports exact replay, not independent replication.
- A generated metric can be reproducible while its target, labels, sampling unit, or interpretation remain invalid.
- Matching structured declarations can be mechanically checked without proving that the declarations describe reality.
- A claim can be literature-supported in one setting but not generalize to IsoPrax or another domain.

## Requirements

### Functional Requirements

- **FR-001**: The manuscript MUST distinguish definitions, repository properties, synthetic findings, literature-supported statements, externally validated findings, and hypotheses.
- **FR-002**: The main cross-family paper MUST remain separate from the model-role study unless the scope decision identifies direct support for a shared research question.
- **FR-003**: Every substantive claim MUST have a unique registry ID, exact wording, evidence category, assumptions, source repository and commit, artifact path and SHA-256, protocol, result or counterexample, uncertainty where relevant, threats to validity, qualification, and manuscript location.
- **FR-004**: Raw records MUST remain unchanged. Any packaged copy MUST preserve the exact uncompressed record bytes and record the source commit and original digest.
- **FR-005**: Independent analysis MUST use raw records for counts, calibration and proper scores, subgroup metrics, bootstrap intervals, disagreements, joint errors, pooling, and run-to-run comparison where those fields exist.
- **FR-006**: Analysis MUST report missing fields and unsupported metrics as unavailable. It MUST NOT infer them from a Markdown summary.
- **FR-007**: The v2.3 freeze record MUST preserve that its bytes were hashed before scored calls and its Git commit was made after Run 1 began.
- **FR-008**: The analysis MUST distinguish exact repeatability on the same frozen cases from replication on new samples, labels, seeds, hosts, or model versions.
- **FR-009**: Adversarial cases MUST cover event, observation-process, horizon, mixture, dependence, calibration-versus-ranking, pooling-harm, and simpler-rule alternatives.
- **FR-010**: The integrity command MUST verify source hashes, recompute registered numerical results, and fail if any numeric claim lacks matching reproducible evidence.
- **FR-011**: The reviewer packet MUST state that automated checks are not independent peer review and must preserve the exclusion of four forecast-calibration revision cases from positive policy-validity claims.
- **FR-012**: The work MUST NOT alter frozen experimental prompts, models, cases, labels, raw records, or preregistered analysis choices.
- **FR-013**: The work MUST NOT create a Semadmit operational rule or claim independent field validation without supporting evidence.

### Key Entities

- **Claim**: A versioned statement with an evidence class, provenance, result, uncertainty, qualification, and paper location.
- **Artifact**: An immutable raw record, generated result, source file, or model identity record with a digest and source commit.
- **Analysis Protocol**: The exact code and commands that derive a result from recorded inputs.
- **Counterexample**: A fixed case that challenges a claim or reveals a false permission or unnecessary refusal.
- **Reviewer Finding**: An open question for external scientific assessment, separate from automated verification.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every substantive main-paper claim has a registry ID and a valid evidence classification.
- **SC-002**: Every numeric claim in the main paper is reproduced by the integrity command from a pinned input or deterministic runner.
- **SC-003**: The integrity command detects at least one deliberately corrupted artifact and one deliberately unregistered numeric claim in tests.
- **SC-004**: All packaged raw snapshots match their source SHA-256 after lossless decompression.
- **SC-005**: The scope decision assigns the model-role work to a separate companion study and does not use it as evidence of JIT/AIOps semantic conformance.
- **SC-006**: The readiness packet reports the external-review and independent-validation gates accurately.

## Assumptions

- The existing PR #54 branch and frozen artifacts remain the provenance base; its history is not rewritten or merged by this work.
- The local analysis package preserves a lossless copy of the pinned Bouleusis records. The source reports `NOASSERTION` for licensing. This does not establish a right to redistribute them; public publication remains blocked until access and redistribution rights are confirmed.
- Literature search cutoff is 2026-10-09; a targeted review does not claim a systematic literature search.
- The scientific reviewer is not available in this execution. A review packet can be prepared, but independent validation cannot be declared complete.
