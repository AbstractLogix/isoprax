# Operation-Specific Policy Challenge: Preregistration

**Status:** Challenge cases and evaluator outcomes are frozen before candidate-policy implementation and scoring. The set is internally authored. It does not provide independent external validation or validate an operational policy.

**Evidence class:** Synthetic and internally authored unless separate case authors and reviewers are added before case freeze.

## Purpose

The existing retrieval pilot compares an operation-specific rule with simpler rules, but its operation-specific path uses evaluator-only root-cause and operation-use labels. Preserve that run as an oracle-informed structural control. This protocol defines a separate challenge with a public-only policy input and reference decisions authored outside the policy implementation.

The primary question is whether an operation-specific candidate reduces false permission or unnecessary refusal beyond a one-label rule and a metadata-only rule. The candidate does not get the reference answer. A result from internally authored cases will not count as independent external validation.

## Case set and unit

Freeze 36 cases before implementing or executing the candidate policy: 12 cases for each declared operation family.

1. Pool forecasts for an explicitly named event or mixture.
2. Compare scores for one common evidence-relevance target.
3. Combine source evidence for a named claim operation.

The case set covers aligned and misaligned targets, different events, different observation processes and windows, changed model revisions, common and duplicate source lineage, unknown provenance, source conflict, explicit and missing mixture weights, calibration transfer, evidence combining, legitimate abstention, and cases where a simple metadata rule is sufficient.

The case is the analysis unit. Cases are authored scenarios, not a sample of independent real-world tasks. Report each operation family separately. Do not pool across the three families.

Store public inputs and evaluator labels in separate files. The public input contains only declared operation context, target identity, score semantics, calibration identity and data split, event or observation window, model revision, source status, source lineage, conflict flags, and the observed numeric outputs. The evaluator file contains the expected operation permission and any reference ranking or threshold decision. Hash and commit both files before policy execution.

The 36-case set was authored internally from the stated challenge dimensions. The evaluator labels are explicitly assigned in the case-authoring record; the candidate policy does not generate them. No outside case author or reviewer took part. These files were committed before the candidate policy implementation:

- Public cases: `docs/experiments/operation-policy-challenge-public.jsonl`, SHA-256 `927f536cf706f80ed52ccf258d826544d45ee95c3e61d79186e4b5d18d116bf1`.
- Evaluator outcomes: `docs/experiments/operation-policy-challenge-evaluator.jsonl`, SHA-256 `e67e7d397b5d686025032aada387f5a2cc8c15b75f09ecadf032afafd80463c7`.
- Case-authoring source: `scripts/build_operation_policy_cases.py`.

If no independent case author or reviewer takes part, record `internal authorship` in the result and do not call the comparison independent external validation.

## Policy inputs and rules

Every candidate function receives the same public input projection. It MUST NOT receive expected permission, gold root cause, hidden operation-use labels, source truth reserved for evaluation, or hidden reviewer outcomes.

Compare these rules:

1. **Naive aggregation:** permit aggregation of all supplied values and apply the declared threshold, if one exists.
2. **One global label:** permit only when the pair has the same frozen global `commensurable` label. Assign one label per score-source pair from declared score metadata before case freeze. Do not change it by operation or case.
3. **Metadata-only:** permit only when declared target, event, observation process, window, score semantics, model revision, verified source status, and source-lineage requirements match. It does not inspect operation-specific admissibility.
4. **Operation-specific candidate:** apply the predeclared requirements for the named operation. Probability pooling requires the same target definition and observation process, compatible horizon/window, development-fitted calibration for that target and exact model revision, and explicit mixture weights when targets differ. Relevance ranking may compare different native score types only after a development-fitted map to the same relevance event and exact score-source revision; raw values remain separate. Evidence combining requires verified provenance, no unresolved conflict, distinct upstream sources, and any declared independent-review condition. Unknown or missing required metadata causes refusal.
5. **Evaluator-only oracle:** read the separate expected labels after the candidate decisions are fixed. It is a reference, never a deployable policy.

Shared model identity, numeric scale, or architecture family alone never permits pooling or counts as independent evidence.

## Outcomes and analysis

Predeclare these outcomes for each policy and operation family:

- false permission rate among reference-invalid operations;
- unnecessary refusal rate and valid-use coverage among reference-valid operations;
- interpretation errors against the named target;
- ranking changes against naive aggregation where a ranking estimand is declared;
- decision changes under the predeclared threshold where a decision rule exists;
- policy input requirements and number of refusals caused by unknown metadata;
- per-case operation cost: policy evaluation steps, metadata bytes, model calls, and required manual reviews.

Use raw per-case outcomes as the primary record. Report denominators. Report paired policy differences by case with exact counts and 95% case-bootstrap intervals (2,000 resamples; seed 4701) only as descriptive uncertainty over the authored set. Do not present the bootstrap as population uncertainty. Report no pooled metric across operation families.

No decision threshold, target mapping, source rule, calibration map, or expected label may change after policy outputs are observed. Any change requires a dated amendment, a new frozen case-set digest, and a new run.

## Integrity checks and stop conditions

- Hash the case files, policy code, global label assignment, target mappings, and preregistration before the first evaluation.
- Audit every helper and derived field in the candidate input path for evaluator-only leakage.
- Add a test that changes evaluator labels while holding public input fixed; candidate decisions must not change.
- Add a test that removes required provenance or target metadata; the candidate must refuse.
- Stop and report `not run` if public and evaluator records cannot be separated or expected decisions are not available before scoring.
- A simpler rule that matches the operation-specific candidate is a valid negative result.
- No Semadmit rule follows from this authored challenge alone.

## Current status

The case files are frozen and unscored. The existing policy result remains available with its oracle-leakage limitation in [the pilot report](retrieval-selection-dependence-results.md). No independent operation-specific validation is supported yet.
