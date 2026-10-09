# Independent Validation and Model-Role Status — 2026-10-08

**Status:** Raw-record reanalysis is complete for the available Bouleusis handoff. The internally authored policy challenge ran, but four forecast cases have calibration-revision errors and the set has no outside review. The model-role suite is blocked by the missing local EmbeddingGemma identity. The prior operation-specific policy comparison remains oracle-informed, not independent validation.

**Evidence class:** Synthetic controlled fixtures and local model runs. These results are not field evidence.

## 1. Evidence inventory and source checks

The new Bouleusis artifacts are analyzed as separate experiments. Shared repository, domain, or fixture ancestry does not make them one estimand.

| Artifact | Raw records | Computed SHA-256 | Record structure |
|---|---:|---|---|
| [Multi-bug retrieval JSONL](https://github.com/AbstractLogix/bouleusis/blob/9f239d6f59cd22e1c1ebf1b9d86b0f28a8fc45b5/docs/experiments/retrieval-multibug-2026-10-08.jsonl) | 1 metadata + 228 runs | `815d2eaaf49941b831f0f20ef3c780dba80c230e76b4424ddba876d12a803921` | 12 cases; 7 arms; budgets: 72 tight, 72 medium, 72 all-evidence, 12 unbounded |
| [VOI policy JSONL](https://github.com/AbstractLogix/bouleusis/blob/9f239d6f59cd22e1c1ebf1b9d86b0f28a8fc45b5/docs/experiments/evidence-acquisition-voi-2026-10-08.jsonl) | 1 metadata + 144 runs | `bd877311c8047f74d38293aebeb0a6024aeec4489e5b416be0240da5f310f568` | 12 cases × 2 budgets × 6 policies |
| [Candidate-score and counterfactual audit JSONL](https://github.com/AbstractLogix/bouleusis/blob/9f239d6f59cd22e1c1ebf1b9d86b0f28a8fc45b5/docs/experiments/evidence-acquisition-audit-2026-10-08.jsonl) | 1 metadata + 543 records | `3689d06770f1c1f0ebad903ae560a2a729984e866c161262ba697ba1f7ddcd59` | 144 candidate-score rows; 144 historical replay comparisons; 38 evaluation-only action outcomes; 216 policy evaluations; 1 analysis record |

The audit metadata's source hashes match the computed multi-bug and VOI hashes. Its preregistration hashes match the current VOI and audit preregistration files. The historical replay comparison reproduces 144/144 matches. The audit says the historical raw records were not rewritten; the stored source JSONL bytes and hash agree.

## Supplied findings not independently reproducible

The multi-bug rows and aggregates can be recomputed, but the raw header's preregistration digest and one report-code digest do not match any reachable source version. Those source versions cannot be reconstructed from this checkout. The raw records remain the source of record; no missing values were inferred from the supplied Markdown summary.

The audit records contain no probability estimates for decision change or abstention resolution. Those prediction-calibration metrics cannot be reproduced or computed. The reported information proxy and task-value proxy are not calibrated probabilities. Other counters below are recomputed from the JSONL rows and are not treated as absent claims from a report.

There is a provenance limit for the multi-bug artifact. Its metadata records preregistration hash `83de5beab888f44ee4ba1cb2f2c940aeef0f97106fbcda2088b728e5e61a393d`, while the current file hash is `b061603564bc8db8c2eccb05248069c43b97f72f8d9dbc00d6b9f567b8c010f5`. That hash is not present in the reachable file history. Of 13 recorded source-file hashes, 12 match the current Bouleusis checkout. The remaining `retrieval_multibug_report.py` hash recorded by the artifact is `c5c8394ad152106f34341b68ba9629eaf8bdf3081d4a49e69a413063dd9eca03`; the current file hash is `fd2a0f98fd51a99d44788f387de04088ec566aeac5b5081739cd60143eac596a`, and no reachable version matches the recorded hash. The raw metadata marks the source worktree dirty. These two source-version mismatches remain unresolved. They do not change the raw JSONL, and the aggregates below were computed from the raw rows.

The raw files are pinned to Bouleusis commit `9f239d6f59cd22e1c1ebf1b9d86b0f28a8fc45b5`. No files in Bouleusis or Semadmit were changed for this analysis.

## 2. Preserved IsoPrax results

The existing [single-bug raw-record reanalysis](bouleusis-retrieval-measurement-validity.md) remains unchanged. It retains 170 outcomes from order perturbations of one injected bug. At the matched 540-byte budget, four bounded selectors were compared. Random included decisive evidence in all ten order trials but succeeded in five. Full context remains a separate unbounded 660-byte reference. The raw records also retain nonzero false-belief persistence for that reference.

The prior two-run local selection/interpreter pilot and the excluded mutable-tag run remain unchanged. The pinned runs matched case sets and selector traces but differed in complete interpreter outputs. These results do not establish field performance or model-role calibration.

Feature 046's earlier internally authored 23-case synthetic challenge reported operation-specific gating at 0/12 false permissions versus 5/12 for metadata-only. Both had 0/11 unnecessary refusals and 0/23 interpretation errors. Ranking changed in 0/4 cases for operation-specific and 1/4 for metadata-only; selected-record decisions changed 0 versus 4. That challenge was built from the candidate conditions. It is an internal structural result, not independent external validation.

## 3. Reproduced multi-bug findings

The 228 run rows contain 12 controlled cases, not 228 independent tasks. Six bounded arms each have 12 runs at each of three budgets. The full-context arm has 12 runs under budget ID `unbounded`.

- Every arm succeeded on all 12 all-evidence rows.
- The unbounded full-context reference succeeded on 12/12 rows. Its mean selected size was 611.75 bytes in this corpus.
- At medium budget, both iterative retrieval arms succeeded on 12/12 rows. Their mean selected size was also 611.75 bytes, equal to the full corpus. They reached full evidence availability in these fixtures.
- At tight budget, no arm succeeded. At medium budget, random one-shot succeeded on 1/12; lexical and EmbeddingGemma one-shot succeeded on 0/12; the oracle positive control succeeded on 11/12.
- The raw epistemic projection contains zero false-belief confidence mass across all 228 rows.

This is a separate corpus from the earlier one-bug sweep. The 611.75-byte mean here is not the earlier 660-byte full-context reference. These results do not show that iterative retrieval saves evidence or cost at medium budget.

## 4. Reproduced VOI and counterfactual audit findings

The 144 VOI rows represent 12 fixtures repeated across two budgets and six policies. The deterministic VOI policy chose retrieval in all 24 fixture-budget states. Its choices exactly matched always-retrieve in all 24 states.

| Budget | Policy | Retrieval choices | Debugging success | Mean acquired bytes | Unnecessary acquisition |
|---|---|---:|---:|---:|---:|
| Tight | Deterministic VOI | 12/12 | 0/12 | 184.17 | 12/12 |
| Tight | Always retrieve | 12/12 | 0/12 | 184.17 | 12/12 |
| Medium | Deterministic VOI | 12/12 | 12/12 | 256.00 | 0/12 |
| Medium | Always retrieve | 12/12 | 12/12 | 256.00 | 0/12 |

False-belief mass did not fall in these VOI runs. The declared success criterion failed: VOI did not acquire fewer bytes than always-retrieve at either budget and did not lower the pooled unnecessary-acquisition rate. The policy did not discriminate from the simpler always-retrieve rule in this fixture set.

The separate audit contains 38 candidate-action outcomes over 24 fixture-budget states and 12 cases: 24 passive retrieval outcomes and 14 diagnostic-test outcomes. The action rows are not 38 independent tasks. I recomputed signed error as prediction minus observed outcome and report the two action families separately.

| Action family | N | Information proxy error / MAE | Task-value proxy error / MAE | Cost v1 error / MAE | Cost v2 error / MAE | Bytes v1 error / MAE | Bytes v2 error / MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| Active diagnostic test | 14 | 0.399 / 0.399 | -0.031 / 0.066 | -0.128 / 0.128 | -0.001 / 0.002 | -160.071 / 160.071 | -1.071 / 2.786 |
| Passive retrieval | 24 | 0.697 / 0.697 | -0.185 / 0.493 | 0.012 / 0.012 | 0.012 / 0.012 | 14.750 / 14.750 | 14.750 / 14.750 |

The information proxy is not a probability of entropy reduction. The task-value proxy is not a task-success probability. Decision-change and abstention-resolution probabilities were not modeled, so their probability errors cannot be measured.

All 24 passive-retrieval candidates had positive predicted net value; 5 had no measured epistemic, decision, or task change, 6 had no entropy reduction, and 12 had no task-success gain. One diagnostic-test candidate had positive predicted net value; it had no entropy or task-success gain. No non-positive-net action had an entropy or task-success gain. These are state-action counts, not independent-task rates.

I also ranked actions by predicted net score within each state that had more than one action. There were 14 such states. The top-scored action was never worse on the observed outcome, but ties account for most comparisons:

| Outcome compared | Concordant | Discordant | Tied outcome | Untied pairs |
|---|---:|---:|---:|---:|
| Entropy reduction | 8 | 0 | 6 | 8 |
| Debugging-success change | 2 | 0 | 12 | 2 |
| Decision change | 2 | 0 | 12 | 2 |

The `14/14 best` summary counts tied outcomes as not worse. Only 2 task-success pairs were untied. The preregistered threshold of at least 10 untied task pairs was not met. This does not support the claim that higher predicted VOI yields greater realized utility. Action families and the two experiments remain separate.

## 5. Operation-specific policy validity

The existing synthetic policy comparison has an oracle-leakage problem. `_reference_permission()` uses hidden gold root-cause and operation-use labels. `_policy_permission("operation_specific", ...)` calls that reference, and `evaluate_policies()` uses the same reference to define the expected permission. The operation-specific ranking and decision paths also read hidden operation-use labels.

The old outputs are preserved as an oracle-informed structural control. They are not an independent result for a deployable candidate. A separate runner now computes candidate decisions only from a schema-limited public record. It computes all candidate outputs before reading the separate evaluator file. A focused test rejects evaluator fields in candidate inputs.

The internally authored version 2 challenge contains 12 cases per operation family and six valid and six invalid outcomes in each family. The public and evaluator records were committed in `fe48a2c66ea3702d696fc1e06241b76360402a49`; the runner was committed in `4e15d884c389518c654da9263d5a5b489dc4ef78` before scoring. Reproduce the scoring with `uv run python scripts/operation_policy_challenge.py`. The full per-case record is [operation-policy-challenge-v2-results.json](../experiments/operation-policy-challenge-v2-results.json), SHA-256 `211cec206853b67f0debe1b8eb33280627dd3ad862c730664e5af492813ab975`. Its input digests are public cases `b5a927f3053aae1a365b9b28d75926cb0b527ba0fc651aadb53839972d6d5f76`, evaluator outcomes `e67e7d397b5d686025032aada387f5a2cc8c15b75f09ecadf032afafd80463c7`, preregistration `9b09e19909825a60002bc5fea9a48b4e231b148f7693142c01966f4f7fa33f36`, and policy runner `747c500f693597235f2ab4cf5ec14cb1bca227311bd2a515833b145c36235e94`. These hashes are also recorded in the [preregistration](operation-specific-policy-validation-preregistration.md).

| Operation family | Policy | False permissions | Unnecessary refusals | Valid-use coverage |
|---|---|---:|---:|---:|
| Forecast pooling | Naive | 6/6 | 0/6 | 6/6 |
| Forecast pooling | Global label | 5/6 | 0/6 | 6/6 |
| Forecast pooling | Metadata-only | 2/6 | 5/6 | 1/6 |
| Forecast pooling | Operation-specific | 0/6 | 4/6 | 2/6 |
| Relevance ranking | Naive | 6/6 | 0/6 | 6/6 |
| Relevance ranking | Global label | 6/6 | 2/6 | 4/6 |
| Relevance ranking | Metadata-only | 3/6 | 5/6 | 1/6 |
| Relevance ranking | Operation-specific | 0/6 | 0/6 | 6/6 |
| Evidence combining | Naive | 6/6 | 0/6 | 6/6 |
| Evidence combining | Global label | 6/6 | 1/6 | 5/6 |
| Evidence combining | Metadata-only | 1/6 | 5/6 | 1/6 |
| Evidence combining | Operation-specific | 0/6 | 0/6 | 6/6 |

The evaluator-only oracle made no errors. It is an upper-bound reference, not a deployable policy. Across the relevance cases, decision-rank errors were 2/10 for naive, 2/8 for global label, 0/4 for metadata-only, and 0/6 for operation-specific. Operation-specific changed the naive ranking in 8/12 cases; metadata-only also changed it in 8/12. For forecast cases with a declared threshold, decision errors were 2/9 for naive, 2/8 for global label, 1/3 for metadata-only, and 0/2 for operation-specific. The eligible denominators differ because a refusing rule produces no ranking or decision.

The challenge exposed four incorrectly labeled valid forecast cases: `FP02`, `FP03`, `FP05`, and `FP06` had calibration records whose model revision did not match the score source. The candidate correctly refused these cases under the frozen exact-revision rule, but the evaluator counted them as unnecessary refusals. The raw outcomes remain unchanged. Therefore the forecast-family comparison is invalid for judging policy value. The current 36-case set was authored internally by the same research effort; no outside author or reviewer checked the expected outcomes. The relevance and evidence-family results are descriptive internal fixture checks, not independent external validation or population error estimates.

Costs were 0, 1, 8, and 12 rule checks per case for naive, global label, metadata-only, and operation-specific. Candidate rules used zero model calls and zero manual reviews. The public input size averaged 1,008 bytes for forecast cases, 1,041.75 for relevance cases, and 913.42 for evidence cases. These are simple input and check-count proxies, not measured runtime or operator costs. Case-bootstrap intervals are stored per operation in the result artifact; they describe only these authored cases.

## 6. Model-role experiment status

The model-role preregistration remains a draft and is not frozen. No scored model-role calls were made. Five runnable identities pass a direct local Ollama digest preflight. The exact EmbeddingGemma candidate does not have a local manifest: both `embeddinggemma-2:740m` and `embeddinggemma-2:740m-bf16` failed to load because this Linux Ollama runtime reports that MLX support is unavailable. Its remote registry digest does not satisfy the local identity gate. The exact Guardian manifest is recorded and verified. The [identity checkpoint](model-role-commensurability-benchmark.md#local-identity-resolution-checkpoint--2026-10-08) records the exact tags, Ollama 0.40.1 runtime, manifest hashes, selected runners, quantization, and available prompt/generation settings for each role.

No alternate embedding model, backend, or runner was substituted. The two complete role-suite runs, calibration, dependence, pooling, specialization, and score-comparability analyses remain unrun. The complete model-role experiment cannot be declared reproduced until all six exact identities resolve and the preregistration is frozen before scoring.

## 7. Evidence classes and conclusions

- **Established repository results:** The earlier 170-run single-bug reanalysis, the two local selection/interpreter runs, Feature 046's authored structural challenge, and the multi-bug and VOI raw-record sets described above. The one-bug and multi-bug results are separate.
- **Literature-supported statements:** No new literature claim is introduced in this report. Existing citations remain in the [retrieval pilot report](retrieval-selection-dependence-results.md) and [model-role protocol](model-role-commensurability-benchmark.md). Those sources do not resolve the local score semantics, oracle leakage, or model-role outcomes here.
- **New experimental findings:** The operation-policy runner produced 36 per-case comparisons. The independently recomputed summary matches the raw result rows. The four forecast fixture-label errors prevent an overall policy-value inference; the relevance and evidence-family outcomes remain internal authored-set observations only.
- **New raw-record findings:** The multi-bug and VOI counts and errors in Sections 3 and 4 were recomputed from their JSONL records. The unresolved multi-bug preregistration and code hashes limit source-version reconstruction.
- **Remaining hypotheses:** Operation-specific gating may add value beyond a metadata-only rule; Tev1 may or may not calibrate across question families; distinct model identities may or may not have dependent errors; score mappings may or may not transfer across target families.

1. **Did operation-specific commensurability provide measurable value beyond simpler rules?** It reduced false permissions on the internally authored relevance and evidence cases, but those results were not independently reviewed. Four forecast cases had invalid calibration-revision metadata, so the current challenge does not support an overall value claim. Feature 046 also showed an internal synthetic difference; neither result establishes deployed value. The VOI policy made the same choices as always-retrieve.
2. **Did shared model identity justify cross-family pooling by itself?** No experiment in this phase tested that claim because the exact EmbeddingGemma identity was unavailable. No repository finding supports using a shared model ID as evidence of semantic equivalence or independence.
3. **Which rules are mature enough for Semadmit operationalization?** None. Preserve provenance, model revision, target, observation window, and unknown status as research metadata. No enforcement rule is justified.
4. **Which hypotheses were weakened or falsified?** Deterministic VOI did not show discriminative value over always-retrieve, and its predicted net score did not show a reliable link to realized task utility in the few untied pairs. The policy runner's first fixture version contained an exact-revision error; the second still has four forecast label errors. This weakens confidence in the internal challenge construction, not the operation-specific hypothesis itself.
5. **What should IsoPrax test next?** Obtain an independent reviewer for operation-policy cases and freeze a corrected forecast-family set before a new run. Resolve the exact EmbeddingGemma identity in the selected runtime or leave model-role scoring blocked. Then freeze the complete six-role preregistration and run two full replays.

**MODEL-ROLE FINDINGS NOT YET REPRODUCED**

**INDEPENDENT OPERATION-SPECIFIC VALIDATION NOT YET SUPPORTED**

**NO SEMADMIT RULE WARRANTED**
