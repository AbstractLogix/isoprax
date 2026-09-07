# Feature Specification: Normative Authority and Commensurability Evidence

**Feature Branch**: `014-normative-commensurability-evidence`

**Created**: 2026-09-07

**Status**: Draft

**Input**: User description: "Vendor the normative Isoprax specification with real numbered anchors, verify every code citation, demonstrate the harm from pooling non-commensurable outcome definitions, reject degenerate calibration, grade commensurability, structure outcome-definition fields with attested equivalence, exercise a third concrete strategy through the knowledge base, and add a public SZZ-based real-world anchor."

## User Scenarios & Testing

### User Story 1 - Verify the normative authority (Priority: P1)

A reviewer can open the repository and follow every normative citation used by
the reference implementation to a numbered section in the vendored Isoprax
v0.3 POC specification.

**Why this priority**: An unverifiable authority makes every MUST and MUST NOT
claim impossible to audit.

**Independent Test**: Run the citation-resolution check against the source
package and confirm that every extracted section reference resolves to a
heading or anchor in the vendored normative document.

**Acceptance Scenarios**:

1. **Given** the repository checkout, **when** a reviewer follows a citation
   such as 5.2, 5.6.3, 8.2, or D.3, **then** the referenced numbered section
   exists in the repository and identifies its normative text.
2. **Given** a source citation with a malformed, absent, or unknown section,
   **when** the citation check runs, **then** the check fails and reports the
   source location and unresolved reference.
3. **Given** generated, cached, or test-fixture files outside the implementation
   package, **when** the citation check runs, **then** those files do not create
   false citation obligations unless explicitly included as normative sources.

### User Story 2 - Assess definitions without circular reasoning (Priority: P1)

A reviewer can compare two Outcome Definitions and see whether they are
identical, bridgeable, attested equivalent, or irreducibly non-commensurable,
with the mismatching dimensions and evidence recorded.

**Why this priority**: A binary refusal hides which differences replay or
additional provenance could resolve, while prose equality produces avoidable
false negatives.

**Independent Test**: Evaluate fixtures that vary one dimension at a time and
verify deterministic classifications, reasons, and provenance requirements.

**Acceptance Scenarios**:

1. **Given** definitions with the same event identity, typed window, typed
   thresholds, and observation process, **when** compared, **then** they are
   classified as directly commensurable even if their display wording differs.
2. **Given** definitions with equivalent semantics but different wording,
   **when** a named attestor supplies a justification and provenance, **then**
   they are classified as attested equivalent and the attestation is included
   in the result.
3. **Given** a recoverable window or threshold difference with sufficient raw
   observations, **when** compared, **then** the result identifies a bridgeable
   mismatch and does not describe it as irreducible.
4. **Given** an event-identity or observation-process mismatch that cannot be
   re-derived from retained observations, **when** compared, **then** the
   result is irreducibly non-commensurable and pooling remains prohibited.
5. **Given** equivalent structured fields in a different serialization order,
   **when** compared, **then** the result is unchanged.

### User Story 3 - See the measurable harm from invalid pooling (Priority: P1)

A reviewer can run a deterministic evidence fixture built from the same
underlying events but two honest outcome windows—seven days and ninety days—
and observe why per-family reporting is required.

**Why this priority**: The non-pooling rule must be supported by a falsifiable
failure mode, not only by asserting that definitions differ.

**Independent Test**: Run the fixture and inspect its per-family calibration,
pooled calibration, and top-k selection results.

**Acceptance Scenarios**:

1. **Given** two families over identical events with seven-day and ninety-day
   defect-detection definitions, **when** each family is evaluated separately,
   **then** both honest calibrations meet the declared ECE threshold of less
   than 0.05.
2. **Given** those same family outputs, **when** pooled calibration is
     calculated, **then** the aggregate ECE remains apparently acceptable while
   the report identifies that this statistic masks definition mismatch.
3. **Given** a declared top-k selection task, **when** pooled ranking is
   compared with per-family ranking against each family’s own outcome, **then**
   pooled selection is measurably worse by a reported deterministic metric and
   the result cannot be labeled cross-family efficacy.
4. **Given** a fixture change that removes the demonstrated degradation,
   **when** the evidence test runs, **then** it fails rather than silently
   weakening the claim.

### User Story 4 - Distinguish calibration from useful prediction (Priority: P1)

A reviewer can tell whether a calibrated declaration also has non-degenerate
discrimination evidence.

**Why this priority**: A constant base-rate predictor can be perfectly
calibrated while carrying no ranking or information value.

**Independent Test**: Evaluate a constant predictor, an informative predictor,
and a predictor whose calibration method collapses scores to the base rate.

**Acceptance Scenarios**:

1. **Given** a constant base-rate predictor, **when** calibration conformance
   is checked, **then** the result is not a qualified calibrated predictor and
   reports the degenerate discrimination evidence.
2. **Given** a predictor with sufficient score variation and declared
   discrimination evidence, **when** calibration and discrimination both pass,
   **then** the report distinguishes the two qualifiers instead of treating
   calibration as predictive usefulness.
3. **Given** missing, undefined, or insufficient discrimination evidence,
   **when** a calibrated declaration is requested, **then** the declaration is
   withheld or marked inconclusive.

### User Story 5 - Exercise all supported strategy types end to end (Priority: P2)

A reviewer can run one concrete strategy of the currently unexercised strategy
type, create a valid ForecastSignal, store it in the knowledge base, and read
it back without confusing coverage with outcome probability.

**Why this priority**: The structural claim about signal semantics is not
credible if only direct test construction exercises it.

**Independent Test**: Run the strategy through signal validation, knowledge-base
write, and round-trip read using deterministic fixture inputs.

**Acceptance Scenarios**:

1. **Given** valid observations and a deterministic strategy configuration,
   **when** a forecast is produced, **then** the resulting signal carries
   outcome probability and does not carry a coverage score as that probability.
2. **Given** a valid signal from the concrete strategy, **when** it is stored
   and retrieved, **then** all normative fields and provenance survive the
   round trip exactly.
3. **Given** an attempt to substitute coverage for outcome probability,
   **when** the signal is validated, **then** it is rejected or explicitly
   reported as invalid.

### User Story 6 - Anchor the failure mode in public label definitions (Priority: P3)

A reviewer can inspect a bounded public-data evidence package that compares two
published SZZ-style defect-label definitions over the same nominal commit set
and identifies their observation-process differences.

**Why this priority**: A public label-definition example provides a realistic
anchor without requiring private telemetry or production adapters.

**Independent Test**: Validate the package’s source manifest, license and
provenance records, aligned event identifiers, definition differences, and
reproducible per-definition ranking summary.

**Acceptance Scenarios**:

1. **Given** the public evidence package, **when** its manifest is checked,
   **then** sources, versions, licenses, retrieval identifiers, and label
   definitions are present.
2. **Given** two label definitions over the same nominal commits, **when**
   aligned, **then** disagreement and observation-process differences are
   reported without silently treating labels as interchangeable.
3. **Given** unavailable, changed, or incompletely licensed public data,
   **when** the evidence package is evaluated, **then** it is reported as
   blocked or inconclusive and no real-world conformance claim is emitted.

### Edge Cases

- A citation may include a subsection such as 5.6.3 or an appendix reference
  such as D.3; resolution must preserve the full reference rather than truncate
  it to a parent section.
- Two structured definitions may serialize lists in different orders; only
  semantically ordered fields may depend on order.
- A bridgeable mismatch must not be treated as resolved without the required
  raw observations and transformation provenance.
- ECE may be undefined for an empty, single-bin, or censored evaluation; the
  result must be explicit rather than passing by omission.
- A top-k comparison must report ties and the selected k deterministically.
- Public evidence may be unavailable or license-incompatible; this is a
  blocked evidence state, not a successful negative result.

## Requirements

### Functional Requirements

- **FR-001**: The repository MUST contain a versioned, self-contained normative
  Isoprax v0.3 POC document with stable numbered sections and appendices that
  cover every normative anchor used by the implementation.
- **FR-002**: The repository MUST document the relationship between the
  vendored normative document and the Stage 0 reference implementation,
  including version, provenance, and any intentionally unsupported sections.
- **FR-003**: Automated verification MUST discover every normative section
  reference in the implementation package and fail on any unresolved or
  malformed reference.
- **FR-004**: Outcome Definitions MUST represent event identity, window,
  thresholds, and observation process as structured, semantically typed data
  rather than free-form prose alone.
- **FR-005**: Window values MUST include duration and anchor semantics;
  threshold values MUST include metric, operator, value, and sustain semantics;
  observation processes MUST identify a defined process kind and its parameters.
- **FR-006**: Definition comparison MUST produce a deterministic graded result
  that distinguishes direct equivalence, attested equivalence, bridgeable
  mismatch, and irreducible mismatch, with dimension-level reasons.
- **FR-007**: An attested equivalence MUST include a named attestor, a
  justification, the attested definitions or canonical identifiers, and
  provenance sufficient for independent review.
- **FR-008**: Cross-family pooling MUST remain prohibited for irreducibly
  non-commensurable definitions and MUST report the graded reason rather than
  collapsing every failure to a bare boolean.
- **FR-009**: The reference evidence MUST include a deterministic same-event
  seven-day versus ninety-day fixture in which each family independently meets
  ECE < 0.05, pooled ECE appears acceptable, and pooled top-k selection is
  measurably worse than per-family selection.
- **FR-010**: Calibration conformance MUST require a non-degenerate
  discrimination qualifier in addition to calibration evidence.
- **FR-011**: A constant or otherwise degenerate predictor MUST NOT receive a
  qualified calibrated declaration, even when its calibration error is below
  the calibration threshold.
- **FR-012**: Discrimination evidence MUST be reported separately from
  calibration and MUST be explicit when undefined, unavailable, or insufficient
  for a declaration.
- **FR-013**: The repository MUST provide one concrete strategy for the
  currently unexercised strategy type and MUST demonstrate its complete path
  through signal validation and knowledge-base round trip.
- **FR-014**: ForecastSignal validation and persistence MUST preserve the
  distinction between outcome probability and coverage.
- **FR-015**: A public SZZ-style evidence package MAY be used as the real-world
  anchor, but it MUST be reproducible, source-attributed, license-aware, and
  fail closed to blocked or inconclusive when its prerequisites are unavailable.
- **FR-016**: The feature MUST NOT claim Semantic or Full Conformance,
  production predictive efficacy, or interchangeability of public labels solely
  from the synthetic or public-label evidence.
- **FR-017**: All new conformance and evidence checks MUST be deterministic for
  fixed inputs and MUST preserve explicit blocked, censored, and inconclusive
  outcomes.

### Key Entities

- **Vendored Normative Specification**: The versioned numbered authority used
  by implementation citations, including provenance and supported scope.
- **Normative Citation**: A source location and full section reference resolved
  against the vendored authority.
- **Outcome Definition**: A structured declaration of event identity, window,
  thresholds, and observation process.
- **Commensurability Assessment**: A graded, dimension-level comparison result
  with evidence and optional attestation provenance.
- **Calibration and Discrimination Report**: Separate diagnostics and
  qualification decisions for reliability and useful score ordering.
- **Pooling Harm Fixture**: A deterministic same-event experiment showing
  acceptable aggregate calibration can coexist with degraded cross-definition
  ranking.
- **Public Label Evidence Package**: Source-grounded, license-aware material
  containing two published label definitions and reproducible comparison output.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of normative section references found in the implementation
  package resolve to the vendored document, with zero unresolved references in
  the focused verification run.
- **SC-002**: The commensurability fixture classifies all defined direct,
  attested, bridgeable, and irreducible cases correctly and reproducibly across
  repeated runs.
- **SC-003**: The seven-day and ninety-day family fixture reports ECE below
  0.05 for each family, an apparently acceptable pooled ECE, and a positive,
  deterministic degradation of pooled top-k selection against the declared
  per-family baseline.
- **SC-004**: 100% of constant-predictor calibration tests withhold the
  qualified calibrated declaration and identify the missing discrimination.
- **SC-005**: The third concrete strategy completes signal validation and
  knowledge-base round trip with exact field and provenance preservation.
- **SC-006**: The public evidence package either reproduces its declared
  comparison from recorded sources or emits an explicit blocked/inconclusive
  result without a real-world conformance claim.
- **SC-007**: Focused feature verification passes without network access for
  the normative, structured-definition, calibration, strategy, and synthetic
  evidence paths.

## Assumptions

- The current externally maintained Isoprax v0.3 POC text can be vendored or
  reconstructed from the authoritative project source with stable section
  numbering; the feature does not invent unsupported normative clauses.
- Existing Stage 0 behavior remains the compatibility baseline unless a
  requirement above explicitly strengthens a false-positive conformance gate.
- Synthetic evidence is suitable for demonstrating a failure mode but is not
  evidence of real-world model performance.
- Public SZZ-style data and publications may be unavailable during ordinary
  offline tests; the public anchor therefore has an explicit blocked state.
- A named attestor is a provenance role, not an automatic authority to change
  the normative specification.
- Existing downstream features retain their current scope and are not silently
  converted into cross-family pooled evaluation.

## Out of Scope

- Private telemetry, production VCS/CI adapters, or online remediation.
- Automatic acceptance of model-generated attestations or canonical data.
- Treating calibration, pooled ECE, or public-label agreement as Semantic or
  Full Conformance.
- Replacing the normative specification with a third-party corpus-admission,
  JEPA/profile, or evaluation framework.
