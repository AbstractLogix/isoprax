# Data Model: Commensurability Experiments and Evidence

These records describe one deterministic synthetic run. They are not new runtime API types.

## ExperimentRun

- `schema_version`: result schema identifier.
- `seed`: deterministic generator seed.
- `synthetic`: always true.
- `claim_boundary`: explicit non-efficacy and non-conformance statement.
- `benchmark_a`: two different-target lanes, valid same-target control, and declared estimands.
- `shared_model`: backend identity, target definitions, target-local scores, uncertainty, ranking, and optional positive-control pool.
- `gate_comparison`: cases, policy definitions, error counts, rank changes, decision changes, and challenge-set limits.

## TargetResult

- `target_id`, `outcome_definition`, `family`, `horizon`.
- `backend_identity` where a predictor is used.
- `n`, positive and negative counts, and observed event rate.
- mean forecast, ten-bin ECE, Brier score, and ROC AUC when both classes occur.
- deterministic 95% percentile intervals and bootstrap method metadata.
- local top-20% counts and explicitly labeled diagnostic global-rank behavior.

## MixtureEstimand

- exact target name and interpretation;
- component target IDs and predeclared weights;
- pooled result metrics;
- a flag stating whether components share one event definition.

## GateCase and GateResult

- operation, declared target relationship, data-quality and operation-precondition fields;
- expected permission and expected interpretation, authored before the run;
- each rule's permission and interpretation;
- false permissions, unnecessary refusals, interpretation errors, ranking changes, and decision changes.

## Metric uncertainty

Each interval records its confidence level, bootstrap method, seed, resample count, and usable resample count. A missing interval or AUC is `null` with a reason.
