# Feature Specification: AI4I 2020 Structural Fixture

**Feature Branch**: `038-ai4i-structural-fixture`

**Created**: 2026-09-22

**Status**: Complete

**Relationship**: This completed feature is the AI4I-specific implementation
record and first dataset example. The shared overview and multi-example
integration principles are maintained in [Feature 039](../039-public-dataset-validation/spec.md).

**Input**: User description: "Add the AI4I 2020 Predictive Maintenance dataset as a bounded sanity-check corpus for Isoprax outcome commensurability, verify its provenance and labels offline, and preserve the boundary between structural evidence and predictive efficacy."

## User Scenarios & Testing

### User Story 1 - Verify a pinned public snapshot offline (Priority: P1)

As an Isoprax maintainer, I want to provide a locally downloaded AI4I 2020
snapshot and receive a deterministic validation report so that the repository can
rely on the dataset without silently fetching or altering external data.

**Why this priority**: Provenance and structural integrity must be established
before any label or commensurability test can be trusted.

**Independent Test**: Supply the pinned UCI CSV to the verifier and confirm the
expected schema, 10,000 data rows, 339 machine-failure rows, failure-mode counts,
content identity, and explicit composite-label discrepancies. Supply a modified
or malformed file and confirm that verification fails closed.

**Acceptance Scenarios**:

1. **Given** the pinned UCI AI4I 2020 CSV, **when** it is verified offline,
   **then** the report records the expected 14-column schema, 10,000 rows,
   339 machine failures, the five mode counts, and the pinned CSV identity.
2. **Given** a CSV with a missing column, duplicate UDI, invalid binary label,
   or changed content, **when** it is verified, **then** verification returns a
   deterministic failure reason and does not repair or reinterpret the data.
3. **Given** no local CSV path, **when** verification is requested, **then** the
   verifier reports that the external snapshot is unavailable and does not make a
   network request.

### User Story 2 - Exercise outcome commensurability boundaries (Priority: P1)

As an Isoprax maintainer, I want explicit outcome definitions for the composite
machine-failure label and its failure modes so that the commensurability guard can
demonstrate why related labels are not automatically poolable with one another or
with JIT defect outcomes.

**Why this priority**: The dataset is valuable primarily as a controlled negative
test for event semantics, not as evidence of production predictive performance.

**Independent Test**: Build the AI4I composite and mode-specific definitions,
compare them through the existing commensurability check, and confirm an
irreducible event mismatch with pooling disabled. Confirm that the label columns
are represented as outcomes rather than prediction inputs.

**Acceptance Scenarios**:

1. **Given** the composite `Machine failure` definition and a mode-specific
   definition such as `TWF`, **when** they are compared, **then** the result is
   irreducible because the events differ and pooling is disallowed.
2. **Given** the AI4I operational definition and an existing JIT defect
   definition, **when** they are compared, **then** the result remains
   non-commensurable; calibration or a shared dataset identifier does not bridge
   the event or observation-process mismatch.
3. **Given** rows with more than one failure mode or a disagreement between the
   composite label and mode flags, **when** the summary is produced, **then** the
   discrepancies are counted and preserved rather than silently normalized.

### User Story 3 - Review bounded evidence and claim limits (Priority: P2)

As a reviewer, I want the dataset source, hashes, license, label semantics, and
claim boundary documented next to the fixture so that another maintainer can
reproduce the check without mistaking it for real-world efficacy evidence.

**Why this priority**: Reproducibility and honest interpretation are required for
the fixture to be useful beyond a local experiment.

**Independent Test**: Review the fixture manifest and quickstart instructions,
then reproduce the offline verification from a locally supplied file without
requiring repository network access.

**Acceptance Scenarios**:

1. **Given** the fixture documentation, **when** a reviewer follows the recorded
   source and checksum instructions, **then** the verifier can reproduce the
   structural summary from a local artifact.
2. **Given** a passing structural verification, **when** a claim is reported,
   **then** it is scoped to public synthetic structural evidence and does not
   claim Semantic/Full Conformance, production efficacy, or real fleet behavior.

### Edge Cases

- The UCI CSV includes a UTF-8 byte-order mark in its header; verification must
  accept the published header while comparing canonical column names.
- The composite label and failure-mode flags are not perfectly aligned in the
  published snapshot; verification must report both mismatch directions.
- Multiple mode flags may be true for one row; mode counts must not be treated as
  mutually exclusive class counts.
- A Kaggle mirror may be used for discovery, but the pinned provenance record
  must identify the UCI artifact and its DOI as the authoritative source.
- A valid structural snapshot is still insufficient for Isoprax replay lineage,
  time-safe prediction, calibration, or efficacy evidence.

## Requirements

### Functional Requirements

- **FR-001**: The verifier MUST accept an explicit local AI4I 2020 CSV path and
  MUST NOT fetch the dataset or require network access during verification.
- **FR-002**: The verifier MUST validate the canonical 14-column schema, row
  shape, unique UDI values, supported product types, numeric sensor fields, and
  binary values for the composite and five mode labels.
- **FR-003**: The verifier MUST compute and report the row count, composite
  failure count and rate, per-mode counts, multi-mode row count, and both
  directions of composite/mode disagreement.
- **FR-004**: The verifier MUST compare the supplied CSV content with the pinned
  source identity and MUST fail closed when the expected checksum or structural
  invariants do not match.
- **FR-005**: The fixture MUST expose separate outcome definitions for the
  composite machine-failure label and mode-specific labels, with an explicit
  current-process sensor observation boundary.
- **FR-006**: Commensurability checks involving the composite and mode-specific
  definitions MUST preserve an irreducible event mismatch and MUST disallow
  pooling; no calibration result may override that decision.
- **FR-007**: The fixture MUST keep failure labels in outcome/diagnostic scope
  and MUST document that using them as model inputs for composite prediction is
  label leakage.
- **FR-008**: The fixture manifest and documentation MUST record the UCI source,
  DOI, license, retrieval reference, artifact and CSV checksums, expected
  structural summary, and explicit non-efficacy claim boundary.
- **FR-009**: Verification failures MUST identify the failed invariant without
  repairing, relabeling, or silently dropping rows.

### Key Entities

- **AI4I snapshot**: A locally supplied CSV artifact identified by source, version,
  license, retrieval reference, checksum, schema, and expected summary.
- **AI4I observation**: One synthetic milling-process row containing identifiers,
  product type, five process/sensor fields, a composite failure label, and five
  failure-mode labels.
- **AI4I outcome definition**: A declared composite or mode-specific event tied
  to the sensor-snapshot observation process and current process-cycle boundary.
- **Structural verification report**: Deterministic counts, checksum status,
  invariant failures, label-disagreement counts, and claim boundary.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The pinned UCI snapshot verifies offline with 10,000 data rows,
  14 columns, 339 composite failures, and the recorded per-mode counts.
- **SC-002**: A changed byte, missing column, duplicate identifier, or invalid
  label causes a failed verification result with a named reason in every case.
- **SC-003**: The verifier reports the published snapshot's composite/mode
  disagreement and multi-mode counts without changing any source row.
- **SC-004**: Composite-versus-mode and AI4I-versus-JIT comparisons produce an
  irreducible or otherwise non-poolable commensurability result in deterministic
  focused tests.
- **SC-005**: The complete focused fixture verification runs without network
  access and without adding a runtime data-science dependency.
- **SC-006**: Documentation and report output state that the result is public
  synthetic structural evidence only, not predictive efficacy or Semantic/Full
  Conformance.

## Assumptions

- The UCI Machine Learning Repository record and DOI `10.24432/C5HS5C` are the
  authoritative source for the pinned artifact; the Kaggle URL remains a mirror
  or discovery reference.
- The repository will not silently download or vendor the full external snapshot;
  the verifier operates on a user-supplied local file and the checked-in fixture
  records its expected identity and summary.
- The published CSV's row order is not treated as a real timestamp or machine
  history, so this feature does not claim forecasting or temporal generalization.
- The fixture is a structural and label-semantics check. It does not satisfy
  Isoprax's replay-lineage, positive/negative evidence-floor, calibration, or
  efficacy requirements.
