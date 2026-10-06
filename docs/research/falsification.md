# Falsification Criteria

IsoPrax must record findings that weaken its research claims. A negative result is a valid result.

## Claims and possible falsifiers

| Claim under test | Finding that weakens or rejects it |
|---|---|
| Family-local calibration adds value beyond global calibration. | Family conditioning does not improve calibration, interpretation, or decision quality on held-out data by a predeclared meaningful amount. |
| Outcome-commensurability checks prevent invalid comparison. | The checks rarely change the operation, its interpretation, or the resulting decision across representative benchmarks. |
| Evidence-family distinctions help. | The distinctions add review and implementation cost without reducing false comparison or decision error. |
| Operation-specific assessment is more precise than one label. | One simple, stable metadata rule achieves the same validity and decision results, with lower complexity. |
| Naive aggregation is unsafe in relevant settings. | Naive aggregation performs equivalently on realistic, provenance-backed benchmarks under multiple declared populations and weights. |
| Outcome semantics affect downstream interpretation. | Different targets, observation processes, windows, or thresholds do not meaningfully change interpretation or decisions in the target use cases. |
| Evidence dependence needs explicit treatment. | Dependence checks do not change uncertainty or conclusions in well-powered tests where shared upstream sources are known. |
| Shared model identity can be mistaken for semantic alignment. | A shared identity adds no false confidence, and output validity is explained by target and observation metadata alone. |
| Separate public data lanes cannot be pooled without alignment. | Cross-family pooling is robust and valid under a rigorous, predeclared common estimand and observation design. This would narrow the claim, not automatically refute all commensurability checks. |

## Study rules

- Predeclare target, operation, population, outcomes, comparator, sample size, and meaningful effect before analysis.
- Include a valid common-target control and a deliberately misaligned target control.
- Report per-family calibration and error before any pooled diagnostic.
- Test at more than one mixture weight when a pooled estimand is proposed.
- Report uncertainty and data quality. A non-significant result from an underpowered study is inconclusive, not falsification.
- Compare operation-specific gates against simple metadata rules and naive aggregation.
- Report all planned outcomes, including results that favor a simpler approach.

## Current synthetic results

The first 23-case authored challenge set gives the operation-specific rule fewer false permissions than the metadata-only rule (0/12 versus 5/12) and the same unnecessary-refusal count (0/11). This supports only the candidate cases encoded in this fixture. It does not establish field performance. Independent case authorship, reviewer agreement, and provenance-backed external tests remain open.

The JEPA experiment uses one backend identity across Change and Operational readouts and across 1-hour and 24-hour windows. Target-local metrics remain separate. Shared identity alone supplies no common event definition. The result is synthetic and does not measure model efficacy.

## Stop or narrow the program when

- repeated, adequately powered public benchmarks show no practical difference between gated and naive operations;
- simple target and provenance metadata resolve the problem without a larger taxonomy;
- a proposed status is unreliable between reviewers or unstable across sources;
- a benchmark result depends on a hidden or post hoc mixture weight;
- the concept adds no value beyond separate per-family reporting.

Such findings should narrow the public scope. They are not reasons to recast a negative result as a request for a larger framework.
