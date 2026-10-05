# Research Data Model: IsoPrax Research-Scope Refinement

These are conceptual records for research and reporting. They are not a new public runtime schema.

## Research Claim

- `statement`: concise claim under review.
- `class`: `repository evidence`, `primary literature`, or `hypothesis`.
- `scope`: target population, outcome family, evidence type, and time context where relevant.
- `source`: repository path, specification clause, or primary literature link.
- `limits`: what the evidence does not establish.

## Operation Assessment

- `evidence_set`: one or more records being considered.
- `target_or_estimand`: the event, construct, population, and horizon to which the operation refers.
- `operation`: comparison, ranking, pooling, calibration transfer, forecast averaging, or evidence combination.
- `context`: prediction time, model version, observation process, and provenance lineage.
- `assumptions`: weighting, dependence, transformation, and missingness assumptions.
- `status`: a proposed result such as `allowed`, `conditional`, `disallowed`, or `unknown`; exact terms remain under study.
- `rationale`: explicit supporting and conflicting evidence.
- `limitations`: unresolved dimensions and valid scope.

An assessment is always scoped to its operation. It does not imply a global relation between the evidence items.

## Benchmark Case

- `case_id` and `question`: stable name and falsifiable question.
- `outcome_definitions`: structured target, observation process, threshold, and horizon for each stream.
- `evidence_generation`: predictor identity, source lineage, score rule, and synthetic or observed status.
- `operation_under_test`: exact aggregation or comparison.
- `valid_control`: a comparable case with an explicit shared target.
- `expected_failure`: unsupported conclusion or measured decision loss under naive aggregation.
- `metrics`: family-local calibration, pooled diagnostics, decision quality, uncertainty, and sample counts as relevant.
- `claim_boundary`: what a result can and cannot support.

## Experiment Protocol

- `hypothesis` and `falsifier`.
- `predictor_identity` and model version.
- `outcome_definitions` and observation process.
- `predeclared splits`, horizon, censoring, and sample-size rules.
- `family-local and pooled measures`.
- `controls`, `results`, and `limitations`.

## Module Disposition

- `module_group` and `current_role`.
- `disposition`: KEEP, REFINE, DEPRECATE, EXTRACT CONCEPTUALLY, or MOVE TO PRIVATE PROJECT.
- `repository_evidence` and `mission_fit`.
- `recommended_next_action` and `risk`.

No module disposition is an automatic change request.
