# Feature Specification: Retrieval and Interpretation Dependence

**Feature Branch**: codex/047-retrieval-selection-dependence
**Created**: 2026-10-08
**Status**: Research design complete; benchmark execution is the next slice
**Input**: User request to study evidence-selection and interpretation dependence, inspired by UNREAL arXiv:2610.08463v1.

## User Scenarios & Testing

### User Story 1 - Separate paper results from IsoPrax hypotheses (Priority: P1)

A research reader needs to know what UNREAL reports and which claims remain untested by IsoPrax.

**Why this priority**: A retrieval-performance result does not by itself answer whether selection and interpretation errors are dependent.

**Independent Test**: Read the literature note and identify the paper's reported outcomes, its limits, the repository's existing results, and the untested hypotheses.

**Acceptance Scenarios**:

1. **Given** the UNREAL paper, **when** the note describes it, **then** it uses the arXiv version 1 title and reports retrieval and answer-quality outcomes within the paper's tested settings.
2. **Given** the same-model dependence question, **when** the note states the evidence, **then** it labels H1-H5 as hypotheses and states that this benchmark has not run.

### User Story 2 - Prepare a controlled benchmark (Priority: P1)

A researcher needs a protocol that can compare lexical, external learned, and model-native selection while holding cases and budgets fixed.

**Why this priority**: The proposed comparison needs controls that isolate selector and interpreter effects.

**Independent Test**: Check that the protocol defines conditions A-D, controls, evidence types, provenance, budgets, metrics, and analysis gates before any result is observed.

**Acceptance Scenarios**:

1. **Given** the four primary conditions, **when** they are compared, **then** A and C hold Model X as interpreter and C and D hold the selector and selected items fixed.
2. **Given** evidence items, **when** they are scored, **then** relevance, source status, and permission for an operation remain separate.
3. **Given** a numeric selector score, **when** a report discusses it, **then** it does not call the score source validity or confidence without a separate validation.
4. **Given** two selectors return evidence for one claim, **when** the benchmark tests corroboration, **then** it reports source overlap, lineage, and false-corroboration results at a fixed total evidence budget.
5. **Given** selector scores and audited source-status labels, **when** the benchmark tests score-as-confidence, **then** it fits calibration on development cases and reports calibration only on held-out cases.

### User Story 3 - Prepare the next experiment slice (Priority: P1)

A research engineer needs a concrete plan to run the benchmark and compare simple policies before any runtime handoff.

**Why this priority**: The research question cannot support implementation or enforcement from a plausible mechanism alone.

**Independent Test**: Confirm that the next-slice steps define reproducibility metadata, held-out policy cases, error dependence, budget effects, falsification, and handoff criteria.

**Acceptance Scenarios**:

1. **Given** a synthetic benchmark result, **when** the report is written, **then** it labels the result synthetic and separates case uncertainty from model and real-world uncertainty.
2. **Given** a proposed Semadmit policy, **when** handoff is considered, **then** the protocol requires a reproducible held-out effect, scope, limits, and falsifier.
3. **Given** Bouleusis relevance, **when** boundaries are stated, **then** IsoPrax studies evidence-selection provenance and does not select evidence or add deliberation logic.

### Edge Cases

- Unknown provenance remains unknown; the experiment does not infer independent sources from missing lineage.
- Duplicate items and items with a common upstream record do not count as separate source coverage.
- A same-model selector proxy is not described as UNREAL.
- A retrieval score is not treated as probability, source validity, or confidence by default.
- If model revisions cannot be pinned, the affected comparison is not reported as completed.
- If no downstream decision rule is declared, the report does not give a decision-change count.
- A null result is reported and may weaken the research direction.

## Requirements

### Functional Requirements

- **FR-001**: The research note MUST separate facts reported by UNREAL, established IsoPrax repository results, new experimental findings, and remaining hypotheses.
- **FR-002**: The paper description MUST use the title and version of the cited primary source and MUST NOT attribute the dependence hypothesis to the paper.
- **FR-003**: The benchmark specification MUST define the four selector/interpreter conditions and the paired comparisons they support.
- **FR-004**: The case protocol MUST include relevant, irrelevant, distracting, misleading, duplicate, shared-upstream, and conflicting items with exact provenance.
- **FR-005**: The benchmark MUST keep relevance, source status, and operation-specific use separate.
- **FR-006**: The protocol MUST define retrieval, interpretation, error-dependence, evidence-budget, and simple-rule measures before execution.
- **FR-007**: The protocol MUST compare naive aggregation, one global label, a metadata-only rule, and operation-specific rules on held-out cases.
- **FR-008**: The report MUST state that no new benchmark findings exist until the protocol is executed.
- **FR-009**: The next-slice plan MUST state reproducibility metadata, controls, falsification conditions, and report outputs.
- **FR-010**: The IsoPrax boundary MUST NOT add a retrieval library, evidence selection for Bouleusis, a general trust engine, deliberation, or runtime enforcement.
- **FR-011**: A Semadmit handoff MUST require a reproducible held-out result with scope, limits, a falsifier, and required runtime metadata.
- **FR-012**: The benchmark MUST test combined evidence from different selectors at equal total budgets and MUST NOT treat selector IDs alone as independent source evidence.
- **FR-013**: The benchmark MUST test whether a held-out calibration of selector scores predicts audited source status, separately from relevance and operation admissibility.

### Success Criteria

- **SC-001**: A reader can state which retrieval and answer-quality results the cited paper reports and which dependence measures it does not report.
- **SC-002**: The protocol contains four primary conditions, paired controls, five evidence budgets, provenance fields, separate evidence properties, and all requested metric classes.
- **SC-003**: The rule comparison includes naive, global-label, metadata-only, and operation-specific alternatives with held-out case evaluation.
- **SC-004**: The next implementation slice has the question, primary conditions, metrics, and preregistration requirements needed to freeze its analysis before a run.
- **SC-005**: The recommendation distinguishes further study from product or runtime implementation.
- **SC-006**: The protocol defines selector-pair corroboration and a held-out score-calibration test against source status.

## Assumptions

- The first execution uses a synthetic case set. It does not establish real-world performance or general model behavior.
- A model-native selector proxy may be used if a full UNREAL implementation is out of scope. The proxy must have a pinned design and must not stand in for UNREAL.
- Feature 046 is relevant repository context, but its synthetic outcome-commensurability results do not answer the retrieval-selection dependence question.
- The document and protocol are the deliverables in this slice. Benchmark implementation and execution remain the next slice.
