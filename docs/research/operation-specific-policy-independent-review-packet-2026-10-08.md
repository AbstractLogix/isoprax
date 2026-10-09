# Operation-Specific Policy Challenge: Independent Review Packet

**Status:** Prepared for an independent reviewer; no independent reviewer was available for this turn. The results remain internally authored findings, not independent validation.

**Evidence class:** Synthetic authored cases and local deterministic policy outputs.

## Review request

Please independently assess whether the expected permissions are correct; whether the cases favor the operation-specific rule; whether the four simpler and candidate rules are fairly specified; whether gold labels leak into policy inputs; and whether the metrics measure the named operations. Do not use this packet to change the frozen v2 outcomes. Record any disagreement as a separate review finding.

## Frozen inputs and source hashes

| Artifact | SHA-256 |
|---|---|
| Version 2 public cases | `b5a927f3053aae1a365b9b28d75926cb0b527ba0fc651aadb53839972d6d5f76` |
| Version 2 evaluator outcomes | `e67e7d397b5d686025032aada387f5a2cc8c15b75f09ecadf032afafd80463c7` |
| Version 2 scored results | `211cec206853b67f0debe1b8eb33280627dd3ad862c730664e5af492813ab975` |
| Version 2 preregistration | `9b09e19909825a60002bc5fea9a48b4e231b148f7693142c01966f4f7fa33f36` |
| Candidate runner | `747c500f693597235f2ab4cf5ec14cb1bca227311bd2a515833b145c36235e94` |
| Case builder | Record in repository history; it is not a frozen external authoring source. |

Version 2 was committed before the complete candidate-policy run. The JSONL files above remain unchanged. The version 2 preregistration's final sentence says the set is unscored, but the result artifact exists. A separate corrigendum records this reporting error without changing the frozen preregistration or its hash.

## Public input and evaluator separation

The public file contains 36 cases, 12 per operation: forecast pooling, relevance ranking, and evidence combining. Candidate functions accept only the declared public schema. The evaluator file is read separately after candidate outputs are fixed. The runner rejects undeclared public fields. Existing focused tests verify that candidate output does not receive evaluator-only fields. The evaluator contains `expected_permission`, `expected_decision`, and `expected_ranking` by case.

The version 2 permission rule requires a development calibration for the exact target and exact model revision. Shared model identity, a numeric range, or architecture family does not establish comparability. The operation-specific rule also requires matching observation process/window for forecast pooling, an explicit weighted mixture for different targets, a common named target for relevance ranking, and valid distinct source lineage for evidence combination. Unknown required metadata causes refusal.

## Four forecast calibration defects

The case builder uses `model-v2` for the right forecast source, while its default calibration helper emits `model-v1`. Four valid-labelled cases inherit that mismatch. Their expected permission is `true`, but the frozen operation-specific rule correctly refuses them.

| Case | Declared targets | Right score-source revision | Right calibration revision | Additional condition | Assessment |
|---|---|---|---|---|---|
| FP02 | Same rain event and target | `model-v2` | `model-v1` | Same-target pooling | Authored metadata defect; permission `true` is unsupported as recorded. |
| FP03 | Rain and snow targets | `model-v2` | `model-v1` | `mixture:regional-weather`, weights 0.5/0.5 | Authored metadata defect; explicit mixture does not repair revision mismatch. |
| FP05 | Same rain event and target | `model-v2` | `model-v1` | Same-target pooling | Authored metadata defect; permission `true` is unsupported as recorded. |
| FP06 | Rain and wind targets | `model-v2` | `model-v1` | `mixture:regional-hazards`, weights 0.25/0.75 | Authored metadata defect; explicit mixture does not repair revision mismatch. |

The fields are schema-valid, so this is not a schema defect. The builder's shared default is the likely cause. No source record demonstrates that a calibration was actually fitted to `model-v2`; correcting the string alone cannot establish calibration quality. The proposed version 3 public input changes only these four right-side calibration revision strings to `model-v2`. It is an unscored proposal and needs reviewer approval before it can become a frozen challenge.

The evaluator's expected decisions need separate review. It contains no underlying event-outcome record or derivation for those labels. For example, FP02 has public scores 0.72 and 0.48, with threshold 0.5, while the evaluator gives expected decision `false`; the runner's unweighted threshold calculation is `true`. This may be an intended hidden event truth, but the source record does not establish it. Do not treat forecast decision-interpretation rates as independently reproducible until the reference standard is supplied and reviewed.

## Case-authoring and expected-result risks

The public cases, evaluator labels, and candidate runner were authored within the same research effort. Each operation's fixtures were built to exercise the declared rule conditions. The operation-specific rule and expected labels therefore share design assumptions. The evaluator did not come from an outside adjudicator or observed task outcome. Case-bootstrap intervals describe only the 12 authored cases in each operation; they are not population uncertainty.

Version 2 produced these false-permission / unnecessary-refusal counts, with denominators of six invalid and six valid cases in each operation:

| Operation | Naive | Global label | Metadata-only | Operation-specific |
|---|---:|---:|---:|---:|
| Forecast pooling | 6/0 | 5/0 | 2/5 | 0/4 |
| Relevance ranking | 6/0 | 6/2 | 3/5 | 0/0 |
| Evidence combining | 6/0 | 6/1 | 1/5 | 0/0 |

The forecast column is not suitable for operation-value inference because of the four mislabeled valid cases and the unresolved event-decision reference. The other two columns are descriptive results on an internally authored fixture set. They do not establish external validity. The apparent advantage is precisely why independent case and label review is needed.

## Baselines, provenance, and metrics

- **Naive aggregation:** permits all supplied values and applies any declared threshold.
- **One global label:** permits when both values have the same frozen `global_label`.
- **Metadata-only:** checks matching target, event, observation process/window, score semantics, model revision, verified source status, and distinct source lineage. It does not inspect calibration fit/split, mixture requirements, or operation-specific conflicts.
- **Operation-specific candidate:** applies the public preregistered requirements for the named operation. It does not read evaluator labels.
- **Evaluator oracle:** copies the evaluator outcome after candidate outputs are fixed. It is an upper-bound reference, not a deployable policy.

The preregistered outcomes are false permission among invalid cases, unnecessary refusal and valid-use coverage among valid cases, interpretation errors, ranking changes against naive aggregation, decision changes under declared thresholds, unknown-metadata refusals, and per-case costs. The preregistration uses 2,000 paired case-bootstrap resamples with seed 4701, separately by operation. Rule checks, public metadata bytes, model calls, and manual review counts are proxies, not measured production costs.

## Known limits and reviewer availability

- All 36 cases and labels are internally authored synthetic scenarios.
- Four forecast permission labels conflict with exact-revision calibration metadata.
- Forecast expected decisions lack a source outcome or reproducible derivation.
- No independent source adjudication or human review was obtained.
- The candidate's no-leakage code path is testable, but the expected labels and case selection can still favor it.
- No population-level error, deployment benefit, or Semadmit enforcement rule follows from this set.

The GitHub repository currently lists only `AbstractLogix` as a collaborator. The PR author is `AbstractLogix`; there are no review requests and no submitted reviews. No independent authorized reviewer was available. No review request was sent to the author as a substitute.

## Prospective version 3 files

These files are proposals only. They preserve all 36 evaluator rows and change only the four right-side calibration `model_revision` fields listed above.

- Public: `docs/experiments/operation-policy-challenge-v3-proposed-public.jsonl`, SHA-256 `82ee4c581ac23aa2df290605b858f48b0b2572224b82b90cfc67b0c58e70aed4`.
- Evaluator: `docs/experiments/operation-policy-challenge-v3-proposed-evaluator.jsonl`, SHA-256 `e67e7d397b5d686025032aada387f5a2cc8c15b75f09ecadf032afafd80463c7`.
- Status: not frozen for execution, not reviewed, and not scored.

The expected decisions, calibration provenance, thresholds, rules, and outcome criteria must be resolved and frozen before any new run. Preserve version 2 and its results as-is.

**Review status:** `INDEPENDENT OPERATION-SPECIFIC VALIDATION NOT YET SUPPORTED`.
