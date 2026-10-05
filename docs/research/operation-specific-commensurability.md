# Operation-Specific Commensurability Proposal

**Status**: Proposal for study; not a new runtime policy.

## Proposal

Do not ask only, “Are A and B commensurable?” Ask: **“May operation O be applied to evidence A and B for target T in context C, under assumptions Z?”**

The answer belongs to the named operation. It must not imply that all other operations are also valid.

## Candidate assessment

Record the evidence items, target or estimand, operation, population, observation process, time window, threshold, censoring, model version, provenance, dependence, assumptions, result, rationale, and limits. Candidate results are `allowed`, `conditional`, `disallowed`, and `unknown`. These names need research before they become normative terms.

## Candidate operation table

| Operation | Minimum candidate conditions | Default when conditions are unknown |
|---|---|---|
| Compare predictive scores or model performance | Same target event or estimand, compatible unit and observation process, aligned evaluation sample, declared metric and weights. Compare calibration and discrimination separately. | Keep target-specific reports separate. |
| Rank scores across families | Same predicted event and relevant horizon, or an explicit decision/utility mapping that explains why different events share one ranking objective. | Do not rank raw scores as one risk quantity. |
| Pool calibration or error metrics | Common outcome meaning and label process, a declared population mixture and weights, compatible censoring and units, and dependence handled in uncertainty estimates. Keep per-family results visible. | Report family results separately. A numeric pooled value alone is not evidence of a common target. |
| Transfer calibration | Same event definition and target population, or a validated transport/recalibration method for the target population, time, and model version. | Recalibrate and validate for the receiving target; do not transfer by score range. |
| Average forecasts | Each forecast describes the same event at the same horizon and prediction time. State the ensemble rule and evaluate the combined forecast on held-out outcomes. Correlated forecasts can be averaged, but their dependence affects uncertainty and does not vanish. | Do not average forecasts for different targets. |
| Combine likelihoods or belief functions | Common hypothesis and prior semantics, justified evidence model, and conditional independence or an explicit dependence model. Track shared source lineage. | Do not multiply or treat evidence as independent because the model names differ. |
| Convert heterogeneous evidence to one confidence value | A validated mapping to a shared target or decision-specific utility with stated assumptions and loss. Preserve original evidence types. | Do not collapse proofs, tests, warnings, observations, and predictions to one scalar. |

These are candidate conditions, not settled rules. An operation may be allowed under an explicit mixture estimand even when separate targets cannot support one universal event probability. Name and report that mixture as its own target.

## Why a global label may be too coarse

Two forecasts may support a within-family calibration report but not a cross-family ranking. Evidence may support pairwise comparison but not independent multiplication. A static test can establish that a declared invariant failed, but it is not a probability forecast. A common `allowed` result for one operation must not imply permission for another.

`OutcomeDefinition` currently provides a bounded outcome-level gate. It compares event, observation process, window, and thresholds. It does not assess all the conditions in this table, and its `pooling_allowed` field must not be presented as a universal evidence-fusion result.

## Test plan

Compare this table with (1) a single global label, (2) a metadata-only rule, and (3) naive aggregation. Test each operation on aligned and misaligned targets, different windows, different observation processes, shifted populations, changed model versions, and shared-source evidence. Measure false permissions, unnecessary refusals, calibration per target, changes in ranking, and decision loss. State the intended mixture and weights before any pooled analysis.

## Literature boundary

Forecast verification makes calibration target-relative; subgroup calibration addresses groups of a prediction population; measurement invariance concerns comparison of particular latent constructs; and conditional-independence rules apply to their stated evidence calculus. These provide foundations and analogies, not proof that the proposed table is complete. See the sources in [the research specification](evidence-commensurability.md#supported-by-adjacent-literature).
