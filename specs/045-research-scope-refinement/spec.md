# Feature Specification: IsoPrax Research-Scope Refinement

**Feature Branch**: `codex/045-research-scope-refinement`

**Created**: 2026-10-05

**Status**: Draft

**Input**: User description: Refine IsoPrax as a public research and reference framework for measurement validity, calibration, outcome semantics, and evidence commensurability. Audit the current repository, state boundaries with Semadmit and Bouleusis, propose operation-specific commensurability, define an invalid-aggregation benchmark and a shared-model experiment, update falsification criteria and the README/research map, and recommend code dispositions. Preserve existing work. Produce a report before any code moves.

## User Scenarios & Testing

### User Story 1 - Understand current scope and boundaries (Priority: P1)

An external researcher can read one report and understand what IsoPrax owns, what the current implementation proves, how its main modules support that mission, and which work belongs to Semadmit or Bouleusis.

**Why this priority**: Readers need a stable public boundary before they can use the research specifications or interpret implementation evidence.

**Independent Test**: A reviewer can answer the final report questions from the report and follow its repository references. The report gives each major module group a KEEP, REFINE, DEPRECATE, EXTRACT CONCEPTUALLY, or MOVE TO PRIVATE PROJECT disposition with a reason.

**Acceptance Scenarios**:

1. **Given** the current repository, **when** a researcher reads the scope report, **then** the report separates normative outcome compatibility, research evidence infrastructure, and product reasoning or enforcement.
2. **Given** a module with no clear product ownership, **when** the audit classifies it, **then** the report does not recommend moving or deprecating it without a concrete reason.
3. **Given** current synthetic, public-data, or replay results, **when** the report describes them, **then** it states their evidence boundary and does not upgrade them to efficacy or Semantic/Full Conformance claims.

### User Story 2 - Evaluate commensurability research (Priority: P1)

An independent researcher can use a public research specification to test when outcome or evidence comparisons, pooling, ranking, calibration transfer, or combination are justified.

**Why this priority**: Operation-specific validity is the proposed next research contribution and must remain a hypothesis until evidence supports it.

**Independent Test**: A reviewer can find the definitions, research questions, candidate assessment record, operation table, at least one invalid-aggregation benchmark, one shared-model experiment, and explicit falsification criteria.

**Acceptance Scenarios**:

1. **Given** two predictions with matching numeric values but different outcomes, **when** the proposal assesses an operation between them, **then** it requires an explicit shared target or a justified decision mapping before permitting interpretation as one risk quantity.
2. **Given** evidence derived from a shared upstream observation, **when** the proposal considers combination, **then** it records dependence and does not assume independence from distinct model names.
3. **Given** new evidence about operation-specific checks, **when** results are reported, **then** established repository evidence, literature-supported claims, and new hypotheses remain distinct.

### User Story 3 - Discover the public research program (Priority: P2)

A new reader can learn IsoPrax's mission and central thesis before reading the Stage 0/1/2 implementation history, then navigate a research map to specifications, evidence, and open work.

**Why this priority**: The repository should communicate its public research identity without erasing useful implementation and reproducibility details.

**Independent Test**: A reader can find the mission, the local-calibration versus cross-outcome distinction, ownership boundaries, current evidence, and next falsifiable question from README and its linked research map.

**Acceptance Scenarios**:

1. **Given** a reader opens the README, **when** they scan its opening section, **then** they see the mission and central thesis before the Stage 0/1/2 details.
2. **Given** a reader wants to investigate a research question, **when** they open the research map, **then** each listed topic points to a relevant report, specification, experiment, or clearly marked open question.
3. **Given** the public/private boundary, **when** a reader follows the Semadmit or Bouleusis link, **then** the page describes public concepts without importing private implementation details.

### Edge Cases

- The existing operation gate may permit pooling only after checking outcome fields; the report must not present it as a universal evidence-combination policy.
- An existing synthetic benchmark may compare different observation windows; the report must not call those targets identical.
- A passing aggregate calibration metric may hide a family-local failure or still refer to different events.
- The same predictor identity may emit forecasts for distinct event definitions or horizons.
- A public dataset may support source, structure, or label-semantics evidence without supporting a shared outcome, efficacy, or production claim.
- The working tree contains unrelated Feature 044 changes; refinement work must preserve them.

## Requirements

### Functional Requirements

- **FR-001**: The project MUST state its public mission as research and reference work on measurement validity, calibration, outcome semantics, and valid comparison across predictive systems.
- **FR-002**: The scope report MUST classify the major current code and documentation groups with one of the requested dispositions and a reason.
- **FR-003**: The report MUST define public responsibilities for IsoPrax, Semadmit, and Bouleusis and state which concepts may flow between them.
- **FR-004**: The research specification MUST treat evidence commensurability and operation-specific commensurability as hypotheses, not established general rules.
- **FR-005**: The operation-specific proposal MUST state preconditions for comparison, ranking, pooling, calibration transfer, probability averaging, and evidence combination, including unknown or conditional outcomes.
- **FR-006**: The invalid-aggregation benchmark MUST include a reproducible synthetic case where numeric compatibility or aggregate calibration does not establish valid shared interpretation.
- **FR-007**: The shared-model experiment MUST use one shared predictor identity with multiple outcome families or horizons and test whether common model identity justifies pooling.
- **FR-008**: The research plan MUST state negative results that would weaken or falsify its central hypotheses.
- **FR-009**: The README MUST explain the mission and thesis before implementation-stage details and link to a research map.
- **FR-010**: The research map MUST distinguish repository evidence, primary literature, hypotheses, and proposed experiments.
- **FR-011**: The refinement MUST NOT move or deprecate implementation code. Any future code disposition MUST remain a recommendation until separately authorized and specified.
- **FR-012**: The refinement MUST preserve existing specifications, experiments, public-data evidence, JEPA reference work, reproducibility records, and unrelated working-tree changes unless the audit gives a concrete reason to change them.

### Key Entities

- **Research claim**: A statement tagged as established by repository evidence, supported by named primary literature, or a new hypothesis.
- **Operation assessment**: A bounded assessment for a named operation, target or estimand, evidence pair or set, context, preconditions, result, rationale, and limitations.
- **Benchmark case**: A reproducible synthetic setup with explicit outcome definitions, operation under test, expected valid and invalid interpretations, and a claim boundary.
- **Experiment protocol**: A predeclared question, model identity, outcome definitions, observations, split, metrics, controls, and falsification rule.
- **Module disposition**: A recommendation to keep, refine, deprecate, extract conceptually, or move to a private project, supported by repository evidence.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All ten requested refinement deliverables are present in linked repository documents.
- **SC-002**: The code audit classifies every major module group and makes no unsupported code-move or deprecation recommendation.
- **SC-003**: At least one invalid-aggregation benchmark and one shared-model experiment are described with controls and measurable outcomes.
- **SC-004**: Every literature-backed statement in the new research documents links to a primary source; hypotheses are labeled as hypotheses.
- **SC-005**: A new reader can locate the mission, boundaries, current evidence, benchmark, experiment, and falsification criteria from the README and research map.
- **SC-006**: No implementation code or existing Feature 044 files are changed by this refinement.

## Assumptions

- The published Isoprax v0.3 POC and the project constitution remain authoritative for existing conformance claims.
- This phase delivers public analysis, research specifications, and navigation documents; it does not implement a new general-purpose evidence-combination runtime or run a new efficacy experiment.
- Existing repository evidence may be summarized only at its demonstrated strength. Public and synthetic evidence remains scoped to its declared dataset, source, and method.
- The new feature record documents this refinement while the existing Feature 044 work remains preserved.
