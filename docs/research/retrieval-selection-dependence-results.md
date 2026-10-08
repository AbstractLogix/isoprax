# Retrieval and Interpretation Dependence: Synthetic Pilot Results

**Evidence class:** Synthetic pilot. These results are not field evidence and are not an UNREAL reproduction.

- Cases: 36 total; 24 held out.
- Case digest: `56bcf8caca2e1a34928784955669d70fc9793b4dd297f14244b0df43679ea3a0`.
- Selection trace digest: `cd30e524ac05975035418488a2c1d14435537af7f043255fad487fd4e97e0738`.
- Full replay matched: `False`.
- Model X: `qwen3.5:9b` via `llamacpp:c97eb11d70b1acdc88af01eef566c1fe4f7fbe93eb1afc06871132f293ff425a` (`c97eb11d70b1acdc88af01eef566c1fe4f7fbe93eb1afc06871132f293ff425a`).
- Model Y: `gemma4:e4b` via `llamacpp:a3d2b95350da03ff9b1943a753bb6617c49a3ee462b632a758518ec817743986` (`a3d2b95350da03ff9b1943a753bb6617c49a3ee462b632a758518ec817743986`).
- Preregistration SHA-256: `4f53eeb361613956ed6999cacee7f2af845f0e70bb9bcdfcd13668b3fceb7742`.
- Scoring-runner SHA-256: `36b36d5c694f75d7922067455dd1eb5cf76982ff0478a816e6afbc611d2ed42b` (the runner used for these runs; later edits only changed reporting and compressed-artifact handling).
- Raw run SHA-256: run 1 `4212cd04740d79fa12efc8fc217733ef43b5792443b21a16c96bf6b3a34d8823`; run 2 `9938c24785aa7677527521f264f4f9d8f449493b744ddfd4346664a647117367`.
- Raw run files are stored as gzip-compressed JSON. The run hashes above are for the decompressed JSON records.
- [Canonical result JSON (gzip)](retrieval-selection-dependence-results.json.gz). Its uncompressed JSON SHA-256 is `a59542495d222f5e34c93dc4428fbeaf79c140e9feb83ded41c7349f2fe74c39`.
- Selector limitation: prompted ranking only; neither selector exposes hidden representations, and Model Y is not retrieval-specialized.

## Replay reproducibility

- Case set matched: `True`; selector traces matched: `True`; complete results matched: `False`.
- Canonical result digests: run 1 `b9c7e50eca8b37b96f1c89b2fa50d4728831193b03da3be047c20a7be22bb405`; run 2 `1b6988ec522d9f88f700299b4ddc14efdb0c44f814bb0b35a522ba7436b08113`.
- Interpretation traces changed in 80/504 records: A 20, B 24, C 36, D 0.
- Among 480 held-out condition/budget rows, parsed field changes were task_success 10, interpretation_error 10, false_belief 10, abstain 11, answer 11, ranking 17.
- The condition and operation-rule tables below show run 1. The next tables show where run 2 changed the outcome summaries.
- An earlier run using mutable model names is retained as `retrieval-selection-dependence-run-mutable-tag-unverified.json.gz` and excluded: the Gemma tag changed during that run, and per-request model revisions were not recorded. A later retry stopped at preflight before scoring.

| Condition | k | Task success (run 1 → run 2) | Interpretation error | False belief | Abstention |
|---|---:|---:|---:|---:|---:|
| A | 1 | 13/24 → 18/24 | 11/24 → 6/24 | 11/24 → 6/24 | 8/24 → 13/24 |
| A | 2 | 11/24 → 12/24 | 13/24 → 12/24 | 13/24 → 12/24 | 5/24 → 6/24 |
| A | 4 | 14/24 → 16/24 | 10/24 → 8/24 | 10/24 → 8/24 | 6/24 → 9/24 |

| Rule | False permissions | Unnecessary refusals | Interpretation errors | Ranking changes | Decision changes |
|---|---:|---:|---:|---:|---:|
| global_label | 161 / 161 | 43 / 43 | 138 / 130 | 120 / 120 | 89 / 89 |
| metadata_only | 79 / 79 | 91 / 91 | 91 / 88 | 250 / 250 | 134 / 134 |
| naive_aggregation | 238 / 238 | 0 / 0 | 138 / 130 | 0 / 0 | 0 / 0 |
| operation_specific | 0 / 0 | 0 / 0 | 70 / 70 | 371 / 371 | 110 / 110 |

- H2 check: C recall exceeded A in 71/120 comparisons in both runs; interpretation error was not lower in 39 cases in run 1 and 46 in run 2.
- H4 lineage log-loss change: run 1 -0.188; run 2 -0.177. Both are descriptive predictions on the authored fixture.

## Selector output handling

One surrounding JSON code fence is removed when present. The runner keeps the first occurrence of each valid item ID, drops repeated or unknown IDs, and appends missing IDs in candidate input order. The report counts these repairs. A response with no valid candidate ID stops the run.

| Selector | Model calls | Raw exact permutations | Repaired calls | Repeated IDs | Unknown IDs dropped | Missing IDs appended |
|---|---:|---:|---:|---:|---:|---:|
| B | 42 | 31 | 11 | 1 | 0 | 10 |
| C | 42 | 27 | 15 | 0 | 0 | 19 |

## Interpreter output handling

The interpreter gets one retry when its JSON output is invalid or its ranking is incomplete. If both attempts fail, the runner records an invalid-output interpretation error. It does not invent missing ranks or count the response as an abstention. Invalid outputs have no root-cause rank and appear in the invalid-output rate.

## Run 1 results by condition and budget

| Condition | k | n | Invalid interpreter output | Retrieval error | Interpretation error | Root-cause accuracy | Recall@k | Complete-evidence recall | Recovery with misleading evidence selected | Conditional error-risk difference (95% CI) | Binary error correlation (95% CI) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| A | 1 | 24 | 0.000 (0) | 1.000 | 0.458 | 0.208 | 0.049 | 0.000 | NA | NA | NA |
| A | 2 | 24 | 0.000 (0) | 1.000 | 0.542 | 0.250 | 0.172 | 0.000 | NA | NA | NA |
| A | 4 | 24 | 0.000 (0) | 0.792 | 0.417 | 0.333 | 0.414 | 0.250 | 0.636 (n=11) | [0.333, 0.722] | 0.434 [0.233, 0.628] |
| A | 8 | 24 | 0.000 (0) | 0.750 | 0.042 | 0.917 | 0.790 | 0.292 | 1.000 (n=12) | [0.000, 0.167] | 0.120 [0.079, 0.243] |
| A | 16 | 24 | 0.000 (0) | 0.417 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 (n=12) | [0.000, 0.000] | NA |
| B | 1 | 24 | 0.000 (0) | 1.000 | 0.000 | 1.000 | 0.189 | 0.000 | NA | NA | NA |
| B | 2 | 24 | 0.000 (0) | 0.125 | 0.000 | 1.000 | 0.378 | 0.875 | NA | [0.000, 0.000] | NA |
| B | 4 | 24 | 0.000 (0) | 0.000 | 0.000 | 1.000 | 0.731 | 1.000 | NA | NA | NA |
| B | 8 | 24 | 0.000 (0) | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 (n=7) | NA | NA |
| B | 16 | 24 | 0.000 (0) | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 (n=12) | NA | NA |
| C | 1 | 24 | 0.000 (0) | 1.000 | 0.000 | 1.000 | 0.189 | 0.000 | NA | NA | NA |
| C | 2 | 24 | 0.000 (0) | 0.125 | 0.000 | 1.000 | 0.378 | 0.875 | NA | [0.000, 0.000] | NA |
| C | 4 | 24 | 0.000 (0) | 0.000 | 0.000 | 1.000 | 0.562 | 1.000 | 1.000 (n=2) | NA | NA |
| C | 8 | 24 | 0.000 (0) | 0.000 | 0.000 | 1.000 | 0.910 | 1.000 | 1.000 (n=9) | NA | NA |
| C | 16 | 24 | 0.000 (0) | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 (n=12) | NA | NA |
| D | 1 | 24 | 1.000 (24) | 1.000 | 1.000 | 0.000 | 0.189 | 0.000 | NA | NA | NA |
| D | 2 | 24 | 1.000 (24) | 0.125 | 1.000 | 0.000 | 0.378 | 0.875 | NA | [0.000, 0.000] | NA |
| D | 4 | 24 | 1.000 (24) | 0.000 | 1.000 | 0.000 | 0.562 | 1.000 | 0.000 (n=2) | NA | NA |
| D | 8 | 24 | 0.958 (23) | 0.000 | 0.958 | 0.042 | 0.910 | 1.000 | 0.111 (n=9) | NA | NA |
| D | 16 | 24 | 0.333 (8) | 0.000 | 0.333 | 0.667 | 1.000 | 1.000 | 0.500 (n=12) | NA | NA |

## Predeclared primary contrast

- Contrast: C minus A; k=4; misleading plus wrong_initial_hypothesis strata.
- Paired cases: 8.
- C-minus-A change in conditional error association: None.
- 95% case-bootstrap interval: None.
- H1 support gate: a point effect of at least 0.15, a positive lower interval, the same direction in both exact replays, and a downstream effect.

## Held-out score calibration against source status

Unknown source status was excluded from calibration and is reported separately. Selector scores are ranking signals; the model-selector score is derived from rank.

| Selector | Development n | Held-out n | Brier | Base-rate Brier | ECE | ROC AUC | Unknown held-out n |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 95 | 380 | 0.040 | 0.040 | 0.029 | 0.845 | 4 |
| B | 95 | 380 | 0.041 | 0.040 | 0.028 | 0.459 | 4 |
| C | 95 | 380 | 0.041 | 0.040 | 0.027 | 0.398 | 4 |

## Run 1 operation-rule comparison

| Rule | False permissions / invalid | Unnecessary refusals / valid | Interpretation errors | Ranking changes | Decision changes |
|---|---:|---:|---:|---:|---:|
| global_label | 161 / 238 | 43 / 242 | 138 | 120 | 89 |
| metadata_only | 79 / 238 | 91 / 242 | 91 | 250 | 134 |
| naive_aggregation | 238 / 238 | 0 / 242 | 138 | 0 | 0 |
| operation_specific | 0 / 238 | 0 / 242 | 70 | 371 | 110 |

The policies were scored against the authored operation reference in this fixture. These counts do not estimate field permission-error rates. The declared downstream decision requires at least two independent verified upstream sources and a 0.60 support share.

## Lineage prediction check

- Held-out metadata-only log loss: 0.6527251613744176.
- Held-out metadata-plus-lineage log loss: 0.4650837224119621.
- Paired change after adding lineage (lower is better): -0.1876414389624555; 95% stratified case-bootstrap interval [-0.209, -0.166].
- This predictive check is descriptive. It does not show a causal lineage effect.

## Selector-pair and repeated-selection probes

- Selector-pair comparisons: 72; exact token-matched comparisons: 72.
- Pair false-corroboration records: 27.
- Repeated-selection records: 18.
- Pair results use one held-out case per stratum and are descriptive. Repeated-selection results concern only the fixed wrong-hypothesis synthetic stratum.

| Pair | k | n | Pair error | Left control error | Right control error | False positive selection | Shared upstream fraction | False corroboration | Exact token matches |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A+B | 16 | 6 | 0.000 | 0.000 | 0.000 | 0.049 | 0.033 | 6 | 6 |
| A+B | 2 | 6 | 0.000 | 0.500 | 0.000 | 0.000 | 0.000 | 0 | 6 |
| A+B | 4 | 6 | 0.000 | 0.500 | 0.000 | 0.000 | 0.000 | 0 | 6 |
| A+B | 8 | 6 | 0.000 | 0.167 | 0.000 | 0.079 | 0.000 | 5 | 6 |
| A+C | 16 | 6 | 0.000 | 0.000 | 0.000 | 0.046 | 0.000 | 5 | 6 |
| A+C | 2 | 6 | 0.000 | 0.500 | 0.000 | 0.000 | 0.000 | 0 | 6 |
| A+C | 4 | 6 | 0.000 | 0.333 | 0.000 | 0.000 | 0.000 | 0 | 6 |
| A+C | 8 | 6 | 0.000 | 0.167 | 0.000 | 0.082 | 0.000 | 5 | 6 |
| B+C | 16 | 6 | 0.000 | 0.000 | 0.000 | 0.029 | 0.033 | 5 | 6 |
| B+C | 2 | 6 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 6 |
| B+C | 4 | 6 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 6 |
| B+C | 8 | 6 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1 | 6 |

| Selector | k | Newly selected n | Supports wrong hypothesis | Contradicts wrong hypothesis |
|---|---:|---:|---:|---:|
| A | 1 | 6 | 0 | 0 |
| A | 2 | 7 | 6 | 0 |
| A | 4 | 11 | 0 | 2 |
| A | 8 | 17 | 0 | 3 |
| A | 16 | 0 | 0 | 0 |
| B | 1 | 3 | 2 | 0 |
| B | 2 | 6 | 3 | 0 |
| B | 4 | 10 | 4 | 0 |
| B | 8 | 5 | 0 | 0 |
| B | 16 | 0 | 0 | 0 |
| C | 1 | 4 | 1 | 1 |
| C | 2 | 6 | 2 | 0 |
| C | 4 | 12 | 3 | 0 |
| C | 8 | 15 | 1 | 0 |
| C | 16 | 0 | 0 | 0 |

## H1-H5 assessment

- **H1_correlated_failure**: not supported by the two-run predeclared gate.
- **H2_retrieval_is_not_epistemic_reliability**: observed in some paired cases.
- **H3_evidence_budget**: descriptive; no monotone assumption.
- **H4_lineage_and_independence**: lineage added predictive value.
- **H5_simpler_rule_may_suffice**: operation-specific rule was no worse than metadata-only on both permission-error counts.

## Evidence classes and limits

- **Established repository results:** Feature 046 contains deterministic synthetic operation-gating and shared-JEPA outcome experiments. Those results do not measure retrieval-selection dependence.
- **Literature-supported:** UNREAL reports retrieval and answer-quality results for its tested settings. It does not report the conditional selection/interpreter error measures in this study. See [UNREAL v1](https://arxiv.org/abs/2610.08463v1).
- **New findings:** The run 1 tables above describe this fixed synthetic case set. The replay matched cases and selector traces but not complete interpreter results. Labels were generator-invariant-checked, not independently expert-adjudicated. Do not treat the run 1 table as a stable two-run estimate or as deployed performance.
- **Remaining hypotheses:** General error dependence, learned-retriever behavior, hidden-representation selection, external populations, and operational policy value remain untested.

## Answers and next test

1. The operation-specific rule changed held-out permission errors versus metadata-only: false permissions delta -79; unnecessary refusals delta -91. This result is limited to the authored fixture. The same permission-error counts appeared in run 2.
2. Shared model identity does not establish semantic equivalence or authorize cross-family pooling. This retrieval pilot does not test cross-target outcome pooling.
3. Only evidence-recording practices are mature enough to propose for Semadmit review: preserve source status, upstream lineage, model revision, and unknown values. This synthetic pilot does not justify an enforcement rule.
4. Any hypothesis not meeting its preregistered gate is weakened or unsupported in this pilot, not disproven generally.
5. Next, test a retrieval-specialized external model and a representation-based Model X selector with held-out real or independently authored evidence; retain the same target-specific and source-status limits.

No Semadmit handoff is made from this synthetic pilot.
