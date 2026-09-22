# Feature Specification: Evidence-Bounded Dataset Examples

**Feature Branch**: `039-public-dataset-validation`

**Created**: 2026-09-22

**Status**: Complete

**Scope**: This is the umbrella specification for the repository's dataset examples. AI4I 2020 is the initial synthetic structural/label-semantics example, with its detailed acceptance record preserved in [Feature 038](../038-ai4i-structural-fixture/spec.md). ApacheJIT, NASA C-MAPSS, and MetroPT-3 extend the set with repository-derived, simulated run-to-failure, and externally anchored operational evidence. The examples share evidence and reporting principles, not one schema, parser, outcome, or generic ingestion adapter.

**Input**: Define and apply a reusable, evidence-bounded approach for documenting, verifying, and comparing multiple Isoprax dataset examples discovered through public sources. Preserve dataset-specific provenance and outcome semantics, offline verification, leakage checks, and fail-closed claim boundaries.

## User Scenarios & Testing

### User Story 1 - Verify distinct dataset examples offline (Priority: P1)

As an Isoprax maintainer, I want to verify locally supplied dataset artifacts
using consistent evidence rules while retaining dataset-specific validation,
so examples can be reproduced without network access or silent
reinterpretation.

**Why this priority**: Provenance and structural integrity are prerequisites
for interpreting any example, whether its labels are synthetic, simulated,
repository-derived, or externally anchored.

**Independent Test**: Run each example's documented verifier against its
locally supplied artifact and confirm that it checks the declared identity and
dataset-specific invariants. Modified, malformed, duplicate, or semantically
invalid input must fail closed.

**Acceptance Scenarios**:

1. **Given** a locally supplied artifact for any listed example, **when** its
   verifier runs, **then** the result identifies the example and reports the
   checks and evidence class appropriate to that dataset.
2. **Given** a changed, malformed, duplicate, or semantically invalid input,
   **when** it is verified, **then** the report names the failed invariant and
   does not repair, relabel, or drop the record.
3. **Given** a dataset-specific diagnostic such as a label discrepancy,
   timestamp inversion, irregular cadence, or censored trajectory, **when** it
   is observed, **then** the report preserves it rather than silently
   normalizing it.

### User Story 2 - Validate temporal operational fixtures (Priority: P1)

As an Isoprax maintainer, I want deterministic checks for NASA C-MAPSS and
MetroPT-3 so that operational observations preserve unit identity, temporal
order, run boundaries, censoring, and externally anchored failure intervals.

**Why this priority**: The examples expose different observation processes,
including current-cycle sensor snapshots, repository commits, held-out
run-to-failure trajectories, and externally anchored operational intervals.

**Independent Test**: Verify C-MAPSS train/test/RUL files and a local MetroPT-3
CSV with explicitly supplied failure intervals. Confirm unit/time order,
schema, row counts, unique keys, RUL alignment, timestamp cadence, and interval
coverage. Missing external intervals or label files must produce an incomplete
or censored result, never inferred negatives.

**Acceptance Scenarios**:

1. **Given** canonical C-MAPSS files, **when** they are verified, **then** each
   FD001-FD004 train/test trajectory has 26 numeric fields, contiguous cycles
   per unit, and one RUL value per test unit.
2. **Given** a MetroPT-3 stream and the four published air-leak intervals,
   **when** it is verified, **then** the report preserves monotonic timestamps,
   unique row identifiers, observed cadence statistics, and rows covered by
   each interval without adding labels to rows outside an anchor.
3. **Given** a missing or contradictory interval anchor, **when** verification
   is requested, **then** the affected observations are withheld or censored
   and no negative outcome is inferred from absence of a label.

### User Story 3 - Publish example selection and claim boundaries (Priority: P2)

As a reviewer, I want a ranked dataset decision ledger, manifests, and outcome
definitions so that each example is interpreted at its correct evidence class
and weaker candidates remain visibly rejected, deferred, or fixture-only.

**Why this priority**: Kaggle is a discovery mirror, not sufficient provenance;
the project must preserve canonical sources, hashes, licenses, and limitations.

**Independent Test**: Review the manifests and run the offline verification
commands on locally supplied artifacts. Confirm AI4I is synthetic structural
evidence, ApacheJIT is repository-derived, C-MAPSS is simulated
run-to-failure/RUL evidence, and MetroPT-3 is external-anchor-dependent
operational evidence. Confirm no report claims cross-family efficacy or
Semantic/Full Conformance.

**Acceptance Scenarios**:

1. **Given** the public-corpus decision ledger, **when** a reviewer inspects it,
   **then** each candidate has a status, evidence class, canonical source,
   artifact identity, label/outcome definition, and explicit limitation.
2. **Given** separate JIT and operational outcome definitions, **when** they are
   compared through the existing commensurability guard, **then** event or
   observation-process mismatches remain irreducible and pooling is disallowed.
3. **Given** a passing structural verifier, **when** a claim is reported,
   **then** it is scoped to the declared corpus and does not become a production,
   replay, predictive-efficacy, or cross-family Semantic claim.

### Edge Cases

- ApacheJIT is not ordered by timestamp in file order; verification must report
  temporal statistics without requiring source order to be sorted.
- ApacheJIT has a known mismatch between its published `year` field and the
  epoch-derived UTC year for some records; the verifier must preserve the count.
- One ApacheJIT project has no `buggy=True` rows; per-project adequacy must not
  be replaced by pooled counts.
- C-MAPSS readme trajectory counts must not override the observed file identity;
  train/test/RUL alignment is checked from the files themselves.
- MetroPT-3 has an empty first-column header in the published CSV and irregular
  timestamp gaps; these are reported, not normalized.
- The UCI MetroPT-3 record gives date/time values without a timezone. Compare
  interval anchors and CSV timestamps as published, without assigning UTC or
  converting offsets; reject timezone-qualified values unless an authoritative
  timezone mapping is added.
- MetroPT-3 has no in-file failure label. Absence of an external interval is not
  an observed negative outcome.
- Kaggle mirrors may change or disappear. Canonical source references and
  content hashes must remain authoritative.
- The verifier must not download data, require pandas/scikit-learn, or vendor
  multi-hundred-megabyte public artifacts.

## Requirements

### Functional Requirements

- **FR-001**: Each verifier MUST accept explicit local artifact paths and MUST
  perform no network access, automatic download, repair, relabeling, or row
  dropping during verification.
- **FR-002**: The ApacheJIT verifier MUST validate its canonical 18-column
  schema, 106,674 rows, unique commit IDs, 15 projects, boolean `buggy`/`fix`
  labels, finite numeric features, epoch timestamps, and pinned SHA-256.
- **FR-003**: The ApacheJIT verifier MUST report project counts, positive and
  negative label counts, per-project positive yield, file-order timestamp
  inversions, and year/epoch discrepancies without treating pooled counts as
  per-project adequacy.
- **FR-004**: The C-MAPSS verifier MUST validate 26 numeric fields, contiguous
  per-unit cycles, train/test unit identities, RUL count alignment, and pinned
  artifact hashes for FD001-FD004.
- **FR-005**: The MetroPT-3 verifier MUST validate the published schema,
  non-empty numeric signals, unique row identifiers and timestamps, monotonic
  time order, cadence statistics, and explicitly supplied failure intervals.
- **FR-006**: MetroPT-3 interval coverage MUST be represented as externally
  anchored outcome evidence; unanchored rows MUST remain unlabeled or censored,
  never inferred negatives.
- **FR-007**: The feature MUST expose outcome definitions that preserve each
  example's event and observation process: AI4I composite/mode failures,
  ApacheJIT bug-inducing commits, C-MAPSS run-to-failure/RUL observations, and
  MetroPT-3 externally reported air-leak failures. Comparisons MUST remain
  non-poolable where the existing commensurability contract finds a mismatch.
- **FR-008**: Manifests MUST record available discovery and canonical source
  references, version, license, artifact hashes, observed counts, evidence
  class, label procedure, and claim boundary for each integrated example.
- **FR-009**: A decision ledger MUST classify the screened candidates, including
  accepted integration candidates, structural-only fixtures, and rejected or
  deferred candidates with reasons.
- **FR-010**: Verification failures MUST identify the failed invariant and
  preserve enough counts to audit the failure; no failure may be converted into
  a passing or neutral result.
- **FR-011**: The repository overview MUST present AI4I, ApacheJIT, C-MAPSS,
  and MetroPT-3 as distinct cases, link their provenance and run instructions,
  and state their different evidence roles and claim limits.

### Key Entities

- **Public dataset snapshot**: A local artifact identified by canonical source,
  mirror reference, version, license, hash, and observed structural summary.
- **AI4I observation**: A synthetic process-cycle row with a composite failure
  outcome and separate failure-mode labels; its detailed contract remains in
  Feature 038.
- **ApacheJIT commit instance**: One repository commit with commit identity,
  project, author epoch, process metrics, and published buggy/fix labels.
- **C-MAPSS engine trajectory**: One engine/unit sequence of operational cycles,
  with train run-to-failure or test RUL evidence.
- **MetroPT-3 observation**: One compressor sensor row keyed by timestamp and
  row identifier, optionally covered by a separately supplied failure interval.
- **Dataset decision**: An evidence class and screening status with explicit
  limitations and claim boundary.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The canonical ApacheJIT artifact verifies offline with 106,674
  rows, 106,674 unique commit IDs, 15 projects, 28,239 buggy rows, 78,435 clean
  rows, and its pinned content hash.
- **SC-002**: Canonical C-MAPSS FD001-FD004 files verify with contiguous cycles
  and exact test/RUL unit alignment; all changed or malformed fixtures fail
  with named reasons.
- **SC-003**: The canonical MetroPT-3 artifact verifies with 1,516,948 rows,
  17 columns, monotonic unique timestamps, observed cadence statistics, and
  explicit row coverage for all four supplied failure intervals.
- **SC-004**: Focused tests prove malformed schemas, changed hashes, duplicate
  identities, non-finite values, broken time order, missing anchors, and label
  leakage are rejected or withheld deterministically.
- **SC-005**: The decision ledger distinguishes real repository-derived labels,
  simulated run-to-failure evidence, externally anchored operational evidence,
  synthetic fixtures, and unavailable/weak candidates.
- **SC-006**: Comparing the integrated dataset outcome definitions with one
  another or with the existing JIT/operational definitions never authorizes
  cross-family pooling merely because scores share a numeric range.
- **SC-007**: Focused verification uses only the Python standard library and
  runs without repository network access or vendored external datasets.
- **SC-008**: The repository overview links all four examples to their
  provenance and verification instructions and distinguishes their evidence
  roles without implying a pooled benchmark.

## Assumptions

- Kaggle is a discovery/mirror surface. Zenodo, NASA, and UCI references are
  the authoritative provenance anchors where available.
- AI4I's detailed structural and label-semantics acceptance criteria are
  preserved in Feature 038; this feature is the shared overview for the complete
  example set.
- ApacheJIT's `buggy` field is preserved as a published repository-derived
  label; this feature does not re-run SZZ or claim that it equals an operational
  deployment failure.
- C-MAPSS is simulated run-to-failure data. It is useful for deterministic
  temporal and RUL mechanics, not real-fleet efficacy.
- MetroPT-3 is one compressor stream. Its externally reported air-leak intervals
  require the UCI source record and do not establish general operational-family
  performance.
- No model training, pooled benchmark score, or Semantic/Full Conformance claim
  is part of this feature; validation is provenance, structure, time-safety, and
  evidence-boundary validation.
