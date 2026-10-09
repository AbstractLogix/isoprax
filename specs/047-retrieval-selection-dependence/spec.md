# Feature Specification: Retrieval and Interpretation Dependence

**Feature Branch**: codex/047-retrieval-selection-benchmark
**Created**: 2026-10-08
**Status**: Synthetic benchmark and policy comparison executed; policy cases include authoring defects and have no outside review. Model-role scoring remains blocked by an unavailable exact local EmbeddingGemma identity.
**Input**: User request to study evidence-selection and interpretation dependence, inspired by UNREAL arXiv:2610.08463v1.

## User Scenarios & Testing

### User Story 1 - Separate paper results from IsoPrax hypotheses (Priority: P1)

A research reader needs to know what UNREAL reports and which claims remain untested by IsoPrax.

**Why this priority**: A retrieval-performance result does not by itself answer whether selection and interpretation errors are dependent.

**Independent Test**: Read the literature note and identify the paper's reported outcomes, its limits, the repository's existing results, and the untested hypotheses.

**Acceptance Scenarios**:

1. **Given** the UNREAL paper, **when** the note describes it, **then** it uses the arXiv version 1 title and reports retrieval and answer-quality outcomes within the paper's tested settings.
2. **Given** the same-model dependence question, **when** the note states the evidence, **then** it labels H1-H5 as hypotheses and distinguishes the completed two-run retrieval/interpreter pilot from the still-unrun model-role benchmark.

### User Story 2 - Prepare a controlled benchmark (Priority: P1)

A researcher needs a protocol that can compare lexical, external learned, and model-native selection while holding cases and budgets fixed.

**Why this priority**: The proposed comparison needs controls that isolate selector and interpreter effects.

**Independent Test**: Check that the protocol defines conditions A-D, controls, evidence types, provenance, budgets, metrics, and analysis gates before any result is observed.

**Acceptance Scenarios**:

1. **Given** the four primary conditions, **when** they are compared, **then** A and C hold Model X as interpreter and C and D hold the selector and selected items fixed.
2. **Given** evidence items, **when** they are scored, **then** relevance, source status, and permission for an operation remain separate.
3. **Given** a numeric selector score, **when** a report discusses it, **then** it does not call the score source validity or confidence without a separate validation.
4. **Given** two selectors return evidence for one claim, **when** the benchmark tests corroboration, **then** it reports source overlap, lineage, and false-corroboration results against single-selector controls matched to the realized item and token budget.
5. **Given** selector scores and audited source-status labels, **when** the benchmark tests score-as-confidence, **then** it fits calibration on development cases and reports calibration only on held-out cases.

### User Story 3 - Prepare the next experiment slice (Priority: P1)

A research engineer needs a concrete plan to run the benchmark and compare simple policies before any runtime handoff.

**Why this priority**: The research question cannot support implementation or enforcement from a plausible mechanism alone.

**Independent Test**: Confirm that the next-slice steps define reproducibility metadata, held-out policy cases, error dependence, budget effects, falsification, and handoff criteria.

**Acceptance Scenarios**:

1. **Given** a synthetic benchmark result, **when** the report is written, **then** it labels the result synthetic and separates case uncertainty from model and real-world uncertainty.
2. **Given** a proposed Semadmit policy, **when** handoff is considered, **then** the protocol requires a reproducible held-out effect, scope, limits, and falsifier.
3. **Given** Bouleusis relevance, **when** boundaries are stated, **then** IsoPrax studies evidence-selection provenance and does not select evidence or add deliberation logic.

### User Story 4 - Compare model roles and score meaning (Priority: P1)

A research reader needs to know whether probabilities, embedding similarities, and critic judgments answer the same question, and whether model role or shared lineage changes calibration and error dependence.

**Why this priority**: A shared numeric range or different model name does not establish a shared target or independent errors.

**Independent Test**: Inspect the frozen model-role protocol and result report. Confirm that every score has a named target, every model has a pinned revision and role, family-specific results are shown, and pooled results name their estimand and weights.

**Acceptance Scenarios**:

1. **Given** Tev1 predictions from several question families, **when** calibration is reported, **then** each family has its own counts, event rate, Brier score, discrimination where meaningful, and uncertainty.
2. **Given** EmbeddingGemma similarity, model-reported probability, and Guardian judgment, **when** their results are compared, **then** each output keeps its original meaning and any common-target calibration is fit on development data and evaluated on held-out data.
3. **Given** Qwen, Gemma, and Guardian judgments, **when** pooling or independence is assessed, **then** the report compares their paired errors and any declared pooling rule against each model alone on the same target and cases.
4. **Given** a coding/debugging task family and non-code controls, **when** Qwen2.5-Coder is evaluated, **then** the report measures role-by-family changes and does not publish a leaderboard ranking.
5. **Given** shared model ancestry, **when** evidence dependence is analyzed, **then** exact model identity and known base/architecture lineage are separate fields; neither names nor lineage alone prove error dependence or independence.

### User Story 5 - Assess Bouleusis retrieval outcomes (Priority: P1)

A research reader needs to know whether reported retrieval recall supports claims about successful investigation, epistemic quality, or iterative retrieval.

**Why this priority**: The supplied sweep has many seed variants but only one independent bug, and its outcomes diverge.

**Independent Test**: Read the measurement-validity report and draft iterative preregistration. Confirm that both label supplied evidence, distinguish outcomes, count bugs as the independent unit, and keep runtime ownership with Bouleusis and Semadmit.

**Acceptance Scenarios**:

1. **Given** decisive-evidence recall and debugging success, **when** the current sweep is assessed, **then** the report treats them as distinct outcomes and does not infer a general predictive rule from one bug.
2. **Given** ten seed variants around one defect, **when** uncertainty and sample size are discussed, **then** the report counts one independent bug and describes seed variation as within-bug repetition.
3. **Given** an iterative retrieval proposal, **when** its protocol is reviewed, **then** it defines equal-budget controls, cost measures, primary and secondary outcomes, and falsification rules before the next scored run.
4. **Given** differing selector identities or score forms, **when** Semadmit handoff is considered, **then** no independence rule is proposed without replicated, held-out downstream effects across distinct bugs.

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
- **FR-012**: The benchmark MUST test combined evidence from different selectors against single-selector controls matched to the realized item and token budget, and MUST NOT treat selector IDs alone as independent source evidence.
- **FR-013**: The benchmark MUST test whether a held-out calibration of selector scores predicts audited source status, separately from relevance and operation admissibility.
- **FR-014**: The initial role comparison MUST include the exact requested identities `qwen3.5:9b`, `gemma4:e4b`, `qwen2.5-coder:7b`, `embeddinggemma-2:740m-bf16`, `tev1:4b`, and `granite4.1-guardian:8b`. If an exact identity cannot run in the selected local runtime, scored model-role work MUST remain blocked. Do not substitute a model, precision, backend, or runner without a dated preregistration amendment before freeze.
- **FR-015**: Each model output MUST be evaluated against a named target. Similarity, probability, confidence, and categorical judgment MUST remain distinct score types.
- **FR-016**: Tev1 MUST be evaluated for calibration on at least three predeclared question families. It MUST report per-family sample counts, event rates, calibration, discrimination where meaningful, and uncertainty.
- **FR-017**: The EmbeddingGemma retrieval score, model-reported probability, and Guardian judgment MUST be compared on a common held-out target where their outputs apply. Any score-to-probability mapping MUST be fit on development cases only.
- **FR-018**: Qwen, Gemma, and Guardian judgments MUST be paired on the same cases and target to measure error overlap and dependence. Any pooling rule MUST have predeclared weights and be compared with its component judgments on held-out cases.
- **FR-019**: Qwen2.5-Coder MUST be compared on a coding/debugging family and at least one non-code control. The analysis MUST report role-by-family effects and MUST NOT reduce the models to one leaderboard.
- **FR-020**: The protocol MUST record exact model revision, declared role, known base or architecture lineage, service version, and output form. Shared lineage or distinct IDs alone MUST NOT justify evidence pooling or independence.
- **FR-021**: Pooled metrics across question families MUST name a mixture estimand and predeclared family weights. Otherwise, report metrics per target only.
- **FR-022**: The Bouleusis measurement-validity report MUST label user-supplied results as not independently reproduced unless trial-level data and configuration are available.
- **FR-023**: The report MUST separate evidence availability, relevance, sufficiency, interpretability, reasoning success, and epistemic correctness.
- **FR-024**: The report MUST identify the independent bug as the unit for multi-bug inference and MUST NOT count seed or order variants around one defect as independent tasks.
- **FR-025**: The prospective iterative-retrieval protocol MUST predefine equal-budget comparisons, verified success, retrieval and reasoning costs, false-repair safeguards, uncertainty units, and falsification rules.
- **FR-026**: The report MUST NOT propose a Semadmit independence rule from selector identity alone; a handoff requires a reproducible held-out association with downstream errors across distinct bugs and a simpler-rule comparison.
- **FR-027**: A deployable policy candidate MUST receive only declared public inputs and MUST NOT receive evaluator-only root causes, hidden operation-use labels, or expected permissions. The evaluator MUST use separately authored reference outcomes.
- **FR-028**: If an existing policy comparison uses its oracle to implement the candidate or answer key, the report MUST preserve it as an oracle-informed control and MUST NOT present it as independent policy evidence.
- **FR-029**: A new policy challenge MUST freeze its case set and expected outcomes before evaluation. It MUST report internal authorship and MUST NOT claim external validation when independent authors or reviewers are absent.
- **FR-030**: A Bouleusis evidence handoff MUST use raw JSONL, verify source hashes, recompute aggregates, keep experiment estimands separate, and report unresolved source-version mismatches.
- **FR-031**: Model-role scoring MUST remain blocked until every requested role has an exact runnable local manifest and the complete preregistration is committed before scored calls.

### Success Criteria

- **SC-001**: A reader can state which retrieval and answer-quality results the cited paper reports and which dependence measures it does not report.
- **SC-002**: The protocol contains four primary conditions, paired controls, five evidence budgets, provenance fields, separate evidence properties, and all requested metric classes.
- **SC-003**: The rule comparison includes naive, global-label, metadata-only, and operation-specific alternatives with held-out case evaluation.
- **SC-004**: The benchmark run is tied to a committed preregistration that freezes its question, primary conditions, model revisions, sample, metrics, and analysis before execution.
- **SC-005**: The recommendation distinguishes further study from product or runtime implementation.
- **SC-006**: The protocol defines selector-pair corroboration and a held-out score-calibration test against source status.
- **SC-007**: All six requested model roles are represented by exact, reproducible model revisions or are explicitly marked unavailable.
- **SC-008**: Tev1 results show calibration separately for each predeclared family; any pooled metric states the mixture estimand and weights.
- **SC-009**: Similarity, probability, and judge labels are evaluated on a shared held-out target before the report makes a commensurability claim.
- **SC-010**: Qwen, Gemma, and Guardian error overlap and the held-out performance of any declared vote or pool are reported against single-model controls.
- **SC-011**: Qwen2.5-Coder is evaluated by family interaction, with no global leaderboard claim.
- **SC-012**: The retrieval measurement report answers all six supplied claim questions and separates evidence status, current findings, and open hypotheses.
- **SC-013**: The next iterative study has a prospective, reviewable protocol with the bug sample, controls, estimands, costs, and decision criteria specified before execution.
- **SC-014**: The prior oracle-informed policy result is clearly separated from any public-input candidate result.
- **SC-015**: The Bouleusis multi-bug and VOI reports show raw-record counts, source hashes, independently recomputed findings, and any provenance discrepancy.
- **SC-016**: The model-role report does not claim findings until both complete, identical, pinned runs are available.

## Assumptions

- The first execution uses a synthetic case set. It does not establish real-world performance or general model behavior.
- A model-native selector proxy may be used if a full UNREAL implementation is out of scope. The proxy must have a pinned design and must not stand in for UNREAL.
- Feature 046 is relevant repository context, but its synthetic outcome-commensurability results do not answer the retrieval-selection dependence question.
- All new model-role cases are synthetic. Guardian's yes/no judge output, Tev1 probability, and embedding similarity retain their model-defined output forms; matching numeric formats do not imply matching semantics.
- A model's advertised role and known lineage are recorded as context. They do not establish empirical skill, calibration, or independence.
- The literature note and first protocol are complete. The current slice executes the selection-dependence benchmark and adds the requested model-role experiments. No model-role result is assumed in advance.
