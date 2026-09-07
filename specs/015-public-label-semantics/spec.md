# Feature Specification: Public Label-Semantics and Split-Sensitivity Evidence

**Feature Branch**: `015-public-label-semantics`

**Created**: 2026-09-07

**Status**: Draft

**Input**: User description: "Build the next research slice: compare supplied public label definitions over shared events, record split and adaptation metadata, and emit fail-closed evidence without claiming Semantic Conformance."

## User Scenarios & Testing

### User Story 1 - Inspect public label semantics (Priority: P1)

A reviewer can provide a small, offline manifest describing published label
definitions and receive a deterministic matrix that identifies which semantic
dimensions agree, differ, or cannot be checked.

**Why this priority**: The research question is whether nominally similar
labels are interchangeable; the first useful answer is an auditable evidence
record, not an adapter or a performance claim.

**Independent Test**: Run supplied fixtures with identical, bridgeable, and
irreducibly different definitions and inspect the stable report.

**Acceptance Scenarios**:

1. **Given** two complete supplied definitions with source identity and
   provenance, **when** the matrix is built, **then** it reports field-level
   agreement and disagreement deterministically.
2. **Given** an event or observation-process mismatch, **when** the matrix is
   built, **then** it records an irreducible or unavailable result and never
   authorizes pooled semantic claims.
3. **Given** a window or threshold mismatch with retained-observation evidence,
   **when** the matrix is built, **then** it records the mismatch as potentially
   bridgeable without treating it as already resolved.

### User Story 2 - Audit evaluation procedure metadata (Priority: P1)

A reviewer can distinguish evidence produced under temporal, random, or
unknown split procedures and can see whether model adaptation and model
version lineage were recorded.

**Why this priority**: Split choice and adaptation can change an evaluation’s
meaning, but neither can establish outcome commensurability by itself.

**Independent Test**: Build reports from fixtures with complete, partial, and
missing procedure metadata and verify explicit statuses and claim boundaries.

**Acceptance Scenarios**:

1. **Given** a source with a declared split, model version, and adaptation
   policy, **when** the report is built, **then** those values survive exactly.
2. **Given** missing or unknown procedure metadata, **when** the report is
   built, **then** it is marked incomplete or inconclusive rather than inferred.
3. **Given** two records with different splits or adaptation policies, **when**
   compared, **then** the report identifies procedural differences without
   calling either result invalid solely from that difference.

### User Story 3 - Preserve blocked evidence (Priority: P1)

A reviewer can tell the difference between a reproduced supplied fixture, an
inconclusive comparison, and evidence blocked by missing snapshots or licensing.

**Why this priority**: A realistic public-data study must not convert missing
access or incomplete provenance into a negative scientific result.

**Independent Test**: Run blocked, changed-identity, and valid manifests and
verify status, reason, and claim scope.

**Acceptance Scenarios**:

1. **Given** unavailable source data or unverified licensing, **when** reduced,
   **then** status is blocked and no comparison claim is emitted.
2. **Given** a changed source identity, **when** reduced, **then** status is
   inconclusive and the recorded reason remains visible.
3. **Given** a valid supplied fixture, **when** reduced, **then** it is labeled
   public-label evidence only and not Semantic/Full Conformance or efficacy.

## Edge Cases

- Source records may list the same aligned event more than once; the report
  must retain the supplied count and not silently deduplicate evidence.
- Definitions may differ only by wording; structured fields, not display text,
  determine the comparison.
- A bridgeable difference without retained observations must remain unresolved.
- Unknown split strategy, model version, or adaptation policy must be recorded
  as unknown rather than defaulted to a safer-looking value.
- Empty source sets, duplicate source identifiers, and negative counts must be
  rejected as malformed input.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST accept only offline, supplied public-label
  evidence manifests and MUST NOT fetch network data as part of reduction.
- **FR-002**: Each source record MUST preserve source identity, published
  version, retrieval reference, license status, and snapshot/checksum identity.
- **FR-003**: Each label record MUST preserve structured outcome-definition
  identity and MUST report dimension-level semantic differences.
- **FR-004**: The report MUST distinguish direct, bridgeable, irreducible, and
  unavailable comparison states without authorizing pooled semantic claims.
- **FR-005**: Bridgeable differences MUST require explicit retained-observation
  evidence and transformation provenance; otherwise they remain unresolved.
- **FR-006**: Each source record MUST preserve split strategy, split reference,
  model version, and adaptation policy when supplied, and MUST preserve unknown
  values when absent.
- **FR-007**: The reducer MUST preserve blocked and inconclusive states for
  unavailable sources, license gaps, changed identities, malformed records, or
  missing required evidence.
- **FR-008**: Reports MUST be deterministic for fixed inputs, including source
  and comparison ordering.
- **FR-009**: Every report MUST state the claim boundary that it is public-label
  evidence only and does not establish Semantic/Full Conformance, predictive
  efficacy, or label interchangeability.

### Key Entities

- **Public Label Definition Record**: A supplied published label definition,
  its structured outcome identity, provenance, and evaluation procedure.
- **Procedure Metadata**: Split, model-version, and adaptation information
  attached to a source record, including explicit unknown values.
- **Label Semantics Comparison**: A deterministic field-level comparison with
  a graded status and evidence requirements.
- **Public Label Semantics Report**: An ordered, fail-closed evidence artifact
  with statuses, reasons, comparisons, and claim boundary.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Supplied equivalent, bridgeable, irreducible, and blocked
  fixtures produce stable reports in focused tests.
- **SC-002**: No report with missing source, license, identity, or required
  bridge evidence produces an authorized pooled semantic claim.
- **SC-003**: Split, model-version, and adaptation metadata round-trip without
  inference or loss when supplied.
- **SC-004**: The implementation remains offline and passes the repository’s
  existing focused and coverage gates.

## Assumptions

- Public datasets and papers may be added later as supplied, license-cleared
  fixtures; this feature does not acquire them.
- Existing structured `OutcomeDefinition` and public-label provenance types are
  the canonical input seams.
- This feature is evidence infrastructure, not corpus admission, model
  training, or a Semantic/Full Conformance expansion.
