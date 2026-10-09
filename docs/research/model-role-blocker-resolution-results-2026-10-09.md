# Model-Role Blocker Resolution and Independent Validation — 2026-10-09

**Evidence class:** Reproduced repository fixtures, synthetic experiments, and
runtime preflight records. No result in this report establishes field
performance or a runtime enforcement rule.

**Status:** Both frozen runs completed. Their raw files are byte-identical,
their integrity checks pass, and the reported point estimates and bootstrap
intervals were independently recomputed from the raw records. The findings are
limited to the fixed synthetic cases and pinned runtime.

## 1. Reproduced findings from preserved records

The earlier machine-readable artifacts remain unchanged. Their stored hashes
were checked in this worktree.

| Artifact | SHA-256 | Reproduction status |
|---|---|---|
| Operation-policy challenge v2 results | `211cec206853b67f0debe1b8eb33280627dd3ad862c730664e5af492813ab975` | Exact match to the recorded result hash. |
| Bouleusis retrieval-sweep reanalysis | `bdef0250d399a0257c0f17edbb514d493ffe58a27bc08b2f4413e3cee0f79dc8` | Stored derived JSON unchanged; raw one-bug records were reanalysed from their pinned source. |
| Feature 046 deterministic results | `02d3642044768c47957221a1e615dc221baf248b97eb4a61c8d75fa8eca80fcd` | Stored machine-readable result hash matches the previously reproduced output. |
| Retrieval-selection run 1 archive | `f26443f0a60cbe08fa46b5a063e53393581e391d5867e9bd8592398116405553` | Preserved archive hash checked. |
| Retrieval-selection run 2 archive | `ab63884072871b96e29591b330d323ac53d1a31ee3d9a995c5644e90df4749c7` | Preserved archive hash checked. |

The Bouleusis source records remain separate experiments, pinned to commit
`9f239d6f59cd22e1c1ebf1b9d86b0f28a8fc45b5`:

| Source record | SHA-256 | Structure |
|---|---|---|
| One-bug retrieval sweep | `0c186de744404ea39a33cc5625c2eaa52a4e6e9c398d489f9d32a237e446fb1c` | 170 order-perturbed outcomes for one injected bug. |
| Multi-bug retrieval | `815d2eaaf49941b831f0f20ef3c780dba80c230e76b4424ddba876d12a803921` | 1 metadata record and 228 run records. |
| Evidence-acquisition VOI | `bd877311c8047f74d38293aebeb0a6024aeec4489e5b416be0240da5f310f568` | 1 metadata record and 144 run records. |
| Candidate-score and counterfactual audit | `3689d06770f1c1f0ebad903ae560a2a729984e866c161262ba697ba1f7ddcd59` | 1 metadata record and 543 records. |

The multi-bug rows and aggregates reproduce from the raw JSONL. Its recorded
preregistration and report-code hashes do not resolve to reachable source
versions. The audit JSONL has no probability estimates for decision changes or
abstention resolution; those metrics remain unavailable. The two-run local
interpreter pilot reproduces case sets and selector traces, but full
interpreter outputs differ. These limits remain as recorded in the
[2026-10-08 status report](independent-validation-and-model-role-status-2026-10-08.md).

## 2. Supplied findings not independently reproducible

The four forecast cases `FP02`, `FP03`, `FP05`, and `FP06` in operation-policy
challenge v2 have valid schema fields but inconsistent calibration provenance:
the right forecast source uses `model-v2`, while its calibration record says
`model-v1`. The evaluator labels all four comparisons valid. Classify these as
incorrectly authored cases, not schema or version defects.

| Case | Proposed operation | Assessment as recorded |
|---|---|---|
| FP02 | Pool two scores for the same rain target. | Deny: the calibration revision does not match the score source. The evaluator's valid label is unsupported. |
| FP03 | Pool rain and snow forecasts as a 0.5/0.5 `regional-weather` mixture. | Deny: the explicit mixture does not repair the calibration-revision mismatch. |
| FP05 | Pool two scores for the same rain target. | Deny: the calibration revision does not match the score source. The evaluator's valid label is unsupported. |
| FP06 | Pool rain and wind forecasts as a 0.25/0.75 `regional-hazards` mixture. | Deny: the explicit mixture does not repair the calibration-revision mismatch. |

These are denials from the public record, not proof that the intended
operations are always invalid. The proposed v3 files only replace four revision
strings; they do not show that calibration was fitted on `model-v2`. A corrected
case is therefore indeterminate until calibration provenance is supplied and
checked. The proposed v3 files remain unscored and unfrozen. Preserve v2 and its
outputs unchanged.

The evaluator's expected threshold decisions also lack source outcomes or a
reproducible derivation. In FP02, scores 0.72 and 0.48 at threshold 0.5 produce
`true` under the runner's unweighted threshold calculation, while the evaluator
labels the expected decision `false`. Do not treat forecast decision
interpretation rates as reproducible policy findings.

No independent human reviewer was available. The repository listed only
`AbstractLogix`, the PR author, as a collaborator; PR #54 had no review request
or submitted review. No request was sent to the author as a substitute for
independent review. The existing
[review packet](operation-specific-policy-independent-review-packet-2026-10-08.md)
remains ready for an external reviewer.

## 3. Interpretation and runtime qualification

The requested Ollama `embeddinggemma-2:740m` and investigated
`embeddinggemma-2:740m-bf16` artifacts do not load on the selected Linux Ollama
0.40.1 runtime because they require MLX. This is a host/backend limitation. It
does not show that the model is unavailable on other supported hosts.

The selected study condition is a distinct, pinned Google checkpoint,
`google/embeddinggemma-2`, revision
`914f7f89142e33e77833254d9c9b90c3cef7303b`, run through SentenceTransformers on
WSL2 Linux x86_64 CPU in float32. The 15 checkpoint-file hashes and package
lock are in the preregistration. The non-scored adapter preflight reproduced
the three saved vectors exactly in the same process. It did not test
cross-process, cross-host, or cross-backend equivalence. No Ollama output was
available for tokenizer, normalization, or numerical parity checks.

Google's [EmbeddingGemma 2 model card](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2)
documents SentenceTransformers use, retrieval prefixes, selective text-only
loading, 768-dimensional vectors, and float32 use on most CPUs. Ollama's
[MLX announcement](https://ollama.com/blog/mlx) describes an Apple Silicon
runtime, but no Mac was available to test the exact requested tag. An Apple
Silicon test remains a candidate follow-up, not an equivalence result.

Preregistration v2.3 SHA-256 by file bytes is
`dc1f009389566e4a2cf1ff5e465c3b2bfb2e41e9b5af7a13ab980ce96b838436`. The runner
records canonical JSON digest `c46b5a446fa74fd50c5c34f5c328e5067241ee4b8298019fc1a8770ee30813b9`.
The exact role identities are Qwen
`c97eb11d70b1acdc88af01eef566c1fe4f7fbe93eb1afc06871132f293ff425a`, Gemma
`a3d2b95350da03ff9b1943a753bb6617c49a3ee462b632a758518ec817743986`, Coder
`dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`, HF CPU
EmbeddingGemma `03f50c93bf327079f38373e5db2937f7826e487bed9e403f51583821737f8462`,
Tev1 `9b5bb969e46c4b776826d6f2d401e22893205693f172653af6254897255025b8`, and
Guardian `f82c0882cec110279601307cdd632d868e29f16eaa59947bef51096e5f740492`.

**Freeze audit:** The v2.3 file, source hashes, prompts, case digest, and model
identities were frozen by SHA-256 before run 1. The Git commit that records
those files (`e254ba0476085cf75bf21f0c1aceaa4d9b954862`) was made after run 1
had started. The scored run used the bytes whose digest is recorded above, and
the runner checked its pinned source and runtime hashes. The commit-before-call
order requested in the brief was not met. Treat this as a provenance limit;
the file was not edited after scoring began.

## 4. New model-role findings

The study is synthetic. It has 64 Tev1 cases in each of three outcome
families, and 32 relevance queries in each of four domains. Each relevance
query has eight items. The predeclared analysis keeps the native score sources
separate and uses only the named relevance target for cross-role comparisons.

### Run integrity, invalid outputs, and repeatability

The repository limits new files to 1 MiB. Each raw JSON is therefore stored as
a deterministic gzip stream split into ten 900 KiB parts. This is lossless.
The [artifact manifest](../experiments/model-role-v2.3-artifact-manifest.json)
records every part hash, the gzip hash, and the original JSON hash. Rebuild a
run file with:

```sh
cat docs/experiments/model-role-v2.3-run-1.json.gz.part-* | gzip -dc > docs/experiments/model-role-v2.3-run-1.json
```

Use `run-2` in the file names to reconstruct the second run.

| Run | Stored artifact | Original JSON SHA-256 | Tev1 rows | Relevance rows | Raw responses | Invalid rows |
|---|---|---|---:|---:|---:|---:|
| 1 | [manifest: run 1](../experiments/model-role-v2.3-artifact-manifest.json) (10 parts) | `cb7e979ec83d500ff29d323635b2c5ff07e2d964f9e4bd63531f029adf0b0fa7` | 192 | 6,144 | 960 | 0 |
| 2 | [manifest: run 2](../experiments/model-role-v2.3-artifact-manifest.json) (10 parts) | `cb7e979ec83d500ff29d323635b2c5ff07e2d964f9e4bd63531f029adf0b0fa7` | 192 | 6,144 | 960 | 0 |

Each reconstructed JSON is 25,036,866 bytes, and the two files are
byte-identical. All 6,144 relevance records have a score and a valid output.
All 192 Tev1 records are valid. The 960 raw-response entries are present and
non-empty. The finalizer reports
matching configuration, predictions, raw responses, and all six model
identities. Its saved summary is
[model-role-v2.3-replay-summary.json](../experiments/model-role-v2.3-replay-summary.json),
SHA-256 `188b716be28d76cdbc2a84e10d3d586297cbed8b40c505b7e9b15f64e761b0e9`.
The per-case comparison found zero differences across the 192 Tev1 rows,
6,144 relevance rows, and 960 raw responses. Both files record case-set digest
`c5fd80e08a3ae494a09ea7d4567cd6b23dbe1e86439e0f78a5fa80ee6c8618c5`, prompt
digest `5c205b125ce95b261eba94bdd0a4dc4918a6717fa3cc839c473d8c69fddde157`,
and result digest
`508d0c328ff63cda5e15baf7c4604187b58c9c61d8cd193ff4daaae69ade1cc2`.
Prediction and raw-response digests are respectively
`6acb7b8f92e6e28c042a3198b194d19281468c8b0aaa0722e956cdbd57744ab5` and
`d9f0a4bb22eb1f24a5d191f3571203a0c79d164f0f866b376f52f6664c2c5826`.

The file equality is strong evidence of repeatability for these exact cases,
prompts, model artifacts, runtime, and seeds. It is not an independent
replication over new tasks, new labels, different seeds, hosts, or model
revisions. The preregistration content was hashed before scoring, but its Git
commit came after Run 1 had started, as recorded in the freeze audit above.

Independent recomputation used the raw rows. It refit each relevance role's
global logistic map from development rows, checked its saved coefficients,
and recomputed held-out counts, event rates, Brier scores, log loss, ECE,
accuracy, AUC, and the declared equal-domain mixture. It also recomputed the
cluster-bootstrap intervals for per-domain and mixture relevance metrics,
Tev1 target metrics, the Tev1 mixture, and both judge pools. These values match
the saved summaries. Per-case disagreement counts and coding comparisons were
also recomputed. All raw rows and responses remain in the lossless archives.

### Tev1 calibration by declared target

Each family has 32 held-out cases. The calibration table reports the probability
vector for that family's own target. These are separate outcome spaces.

| Target | Held-out class counts | Accuracy | Brier (95% CI) | Log loss (95% CI) | AUC (95% CI) | ECE |
|---|---|---:|---:|---:|---:|---:|
| Equipment binary | false 16, true 16; event rate 0.50 | 1.000 | 0.010441 [0.008126, 0.012648] | 0.070880 [0.062011, 0.079397] | 1.000 [1.000, 1.000] | 0.068114 |
| Software category | 8 in each of four fault classes | 1.000 | 0.000002432 [0.000001954, 0.000002917] | 0.001189 [0.001030, 0.001330] | 1.000 [1.000, 1.000] | 0.001189 |
| Incident ordinal | 8 in each of four severity classes | 1.000 | 0.000001009 [0.000000775, 0.000001260] | 0.000768 [0.000682, 0.000858] | 1.000 [1.000, 1.000] | 0.000768 |

The predeclared equal-weight family estimand is expected held-out log loss when
one family is sampled uniformly from the three authored families. It is
`0.024279` (95% CI `0.021474–0.027337`), with weights `1/3` per family. It is
a mixture of losses, not a probability pool. The low errors on these balanced,
authored cases do not establish calibration on natural questions. Ordinal
threshold and ranked-probability outputs for the nominal software categories
are not interpreted because those classes have no declared order.

### Common-target relevance metrics by role and domain

Each domain has 128 held-out item rows across 16 queries, with 48 relevant
items (event rate 0.375). Brier, log loss, ECE, and AUC use the role's
development-fitted global calibration map. The AUC values equal the native
raw-score AUCs in these rows. MRR and Recall@3 use the native raw score. The
stored records also report Recall@1 and Recall@5. Intervals are 95%
query-cluster bootstrap intervals.

| Role / domain | Brier (95% CI) | Log loss | ECE | AUC (95% CI) | MRR / Recall@3 |
|---|---:|---:|---:|---:|---:|
| Qwen / equipment | 0.008806 [0.002889, 0.020641] | 0.044569 | 0.041160 | 1.000000 [1.000000, 1.000000] | 1.000 / 1.000 |
| Qwen / software | 0.003355 [0.002889, 0.004054] | 0.039583 | 0.038715 | 1.000000 [1.000000, 1.000000] | 1.000 / 1.000 |
| Qwen / policy | 0.002889 [0.002889, 0.002889] | 0.037367 | 0.036624 | 1.000000 [1.000000, 1.000000] | 1.000 / 1.000 |
| Qwen / safety | 0.067861 [0.028094, 0.114303] | 0.131984 | 0.015508 | 0.996354 [0.992839, 1.000000] | 1.000 / 1.000 |
| Gemma / equipment | 0.210305 [0.075923, 0.389400] | 0.343804 | 0.038845 | 0.916667 [0.833333, 0.979167] | 1.000 / 0.833 |
| Gemma / software | 0.051154 [0.044894, 0.061159] | 0.140281 | 0.114950 | 1.000000 [1.000000, 1.000000] | 1.000 / 1.000 |
| Gemma / policy | 0.030599 [0.026592, 0.035610] | 0.109018 | 0.100172 | 1.000000 [1.000000, 1.000000] | 1.000 / 1.000 |
| Gemma / safety | 0.029063 [0.026143, 0.031897] | 0.102766 | 0.094412 | 1.000000 [1.000000, 1.000000] | 1.000 / 1.000 |
| Qwen2.5-Coder / equipment | 0.006587 [0.006415, 0.006903] | 0.053903 | 0.052169 | 1.000000 [1.000000, 1.000000] | 1.000 / 1.000 |
| Qwen2.5-Coder / software | 0.006847 [0.006415, 0.007278] | 0.054959 | 0.053155 | 1.000000 [1.000000, 1.000000] | 1.000 / 1.000 |
| Qwen2.5-Coder / policy | 0.006415 [0.006415, 0.006415] | 0.053068 | 0.051380 | 1.000000 [1.000000, 1.000000] | 1.000 / 1.000 |
| Qwen2.5-Coder / safety | 0.006724 [0.006612, 0.006809] | 0.055322 | 0.053554 | 1.000000 [1.000000, 1.000000] | 1.000 / 1.000 |
| EmbeddingGemma / equipment | 0.465835 [0.465691, 0.466003] | 0.658456 | 0.000464 | 0.805208 [0.786452, 0.823958] | 1.000 / 0.667 |
| EmbeddingGemma / software | 0.467056 [0.466907, 0.467219] | 0.659762 | 0.003106 | 0.982292 [0.968229, 0.994010] | 1.000 / 0.979 |
| EmbeddingGemma / policy | 0.469346 [0.469218, 0.469477] | 0.662198 | 0.001749 | 0.363802 [0.328379, 0.398438] | 0.388 / 0.250 |
| EmbeddingGemma / safety | 0.470221 [0.470072, 0.470403] | 0.663127 | 0.002048 | 0.247135 [0.206764, 0.276563] | 0.242 / 0.063 |
| Tev1 / equipment | 0.006416 [0.005995, 0.006850] | 0.050202 | 0.048508 | 1.000000 [1.000000, 1.000000] | 1.000 / 1.000 |
| Tev1 / software | 0.216644 [0.191492, 0.242089] | 0.341690 | 0.070758 | 0.973958 [0.960417, 0.987240] | 1.000 / 0.958 |
| Tev1 / policy | 0.009739 [0.008684, 0.010844] | 0.065297 | 0.062701 | 1.000000 [1.000000, 1.000000] | 1.000 / 1.000 |
| Tev1 / safety | 0.004738 [0.004378, 0.005066] | 0.043911 | 0.042672 | 1.000000 [1.000000, 1.000000] | 1.000 / 1.000 |
| Guardian / equipment | 0.468752 [0.468752, 0.468752] | 0.661565 | 0.000993 | 0.500000 [0.500000, 0.500000] | 1.000 / 0.667 |
| Guardian / software | 0.468752 [0.468752, 0.468752] | 0.661565 | 0.000993 | 0.500000 [0.500000, 0.500000] | 1.000 / 0.667 |
| Guardian / policy | 0.468752 [0.468752, 0.468752] | 0.661565 | 0.000993 | 0.500000 [0.500000, 0.500000] | 1.000 / 0.667 |
| Guardian / safety | 0.468752 [0.468752, 0.468752] | 0.661565 | 0.000993 | 0.500000 [0.500000, 0.500000] | 1.000 / 0.667 |

Guardian emitted the same native score (`0`) for all held-out items. Its
reported MRR and Recall@3 are tie-order artifacts from sorting by item ID and
do not measure useful ranking. Its 0.625 accuracy equals the always-negative
baseline for the 0.375 event rate. EmbeddingGemma's cosine score has strong
ranking in the authored software domain but AUC below 0.5 in policy and safety.
Its globally calibrated Brier scores stay near the constant-base-rate Brier
of 0.46875. The small ECE values do not offset the weak Brier and log loss.
These outputs do not make cosine similarity commensurable with model
probability or critic judgment.

For each individual score source, the only cross-domain summary is the
predeclared equal-weight mixture of the four common-target domains. Each domain
has weight 0.25. It is an expected metric over domains, not a pooled relevance
probability. The judge-pool predictors are separate predeclared analyses below.

| Role | Brier (95% CI) | Log loss (95% CI) | AUC (95% CI) | Accuracy |
|---|---:|---:|---:|---:|
| Qwen | 0.020728 [0.010039, 0.033088] | 0.063376 [0.047455, 0.081015] | 0.999089 [0.998210, 1.000000] | 0.986328 |
| Gemma | 0.080280 [0.045931, 0.123379] | 0.173967 [0.128486, 0.231790] | 0.979167 [0.963542, 0.994792] | 0.966797 |
| Qwen2.5-Coder | 0.006644 [0.006522, 0.006787] | 0.054313 [0.053738, 0.054943] | 1.000000 [1.000000, 1.000000] | 1.000000 |
| EmbeddingGemma | 0.468115 [0.468040, 0.468198] | 0.660886 [0.660807, 0.660970] | 0.599609 [0.585609, 0.613153] | 0.625000 |
| Tev1 | 0.059384 [0.053078, 0.065771] | 0.125275 [0.118730, 0.131530] | 0.993490 [0.990299, 0.996810] | 0.958984 |
| Guardian | 0.468752 [0.468752, 0.468752] | 0.661565 [0.661565, 0.661565] | 0.500000 [0.500000, 0.500000] | 0.625000 |

### Case-level disagreement, pools, and specialization

There are 512 held-out item judgments per judge pair (64 queries). The first
column below counts different binary judgments. The next counts items on which
both models were wrong. The development-only product is the expected joint
error rate under an independence assumption; it is shown as a reference, not
as evidence that errors are independent.

| Judge pair | Different judgments | Joint errors in held-out rows | Development product under independence |
|---|---:|---:|---:|
| Qwen + Gemma | 8 / 512 | 0 / 512 | 0.00001144 |
| Qwen + Guardian | 199 / 512 | 0 / 512 | 0.00219727 |
| Gemma + Guardian | 193 / 512 | 0 / 512 | 0.00073242 |

All pairs also had zero false-positive and zero false-negative overlap. The
held-out joint-error bootstrap interval is `[0, 0]` because no joint error was
observed in these authored cases. This does not establish independence or a
zero population error rate. The result is weak evidence about error dependence
because the general models made very few development errors and the fixtures
are easy.

The declared judge pools use equal model weights (`1/3`) and the same
equal-domain mixture (`1/4` per domain), with 512 / 512 coverage.

| Predictor | Accuracy | AUC | Brier (95% CI) | Log loss (95% CI) | FPR / FNR |
|---|---:|---:|---:|---:|---:|
| Qwen alone | 0.986328 | 0.999089 | 0.020728 [0.010039, 0.033088] | 0.063376 [0.047455, 0.081015] | not pooled |
| Majority hard-label pool | 1.000000 | 1.000000 | approximately 0 | approximately 0 | 0 / 0 |
| Equal-weight calibrated-probability pool | 1.000000 | 1.000000 | 0.103582 [0.095703, 0.112246] | 0.247340 [0.237626, 0.258619] | 0 / 0 |

The majority pool encodes its vote as a zero-or-one score. It is not a
calibrated probability. The equal-weight probability pool has perfect
classification on these rows but worse Brier score and log loss than Qwen
alone. Pooling did not improve every proper score in this fixture. Neither
pool result establishes general model quality or independence.

The coding-specialized model was compared with Qwen and Gemma over 16 held-out
queries per domain. The differences below are paired per-query item accuracy.

| Domain | Coder minus Qwen accuracy (95% CI) | Top item differs from Qwen | Coder minus Gemma accuracy (95% CI) | Top item differs from Gemma |
|---|---:|---:|---:|---:|
| Equipment | +0.0078 [0.0000, 0.0234] | 0 / 16 | 0.0000 [0.0000, 0.0000] | 0 / 16 |
| Software | 0.0000 [0.0000, 0.0000] | 0 / 16 | +0.0078 [0.0000, 0.0234] | 0 / 16 |
| Policy | 0.0000 [0.0000, 0.0000] | 0 / 16 | 0.0000 [0.0000, 0.0000] | 0 / 16 |
| Safety | +0.0469 [0.0156, 0.0781] | 0 / 16 | 0.0000 [0.0000, 0.0000] | 11 / 16 |

On safety, Coder and Gemma had the same average per-item accuracy but selected
different top items in 11 of 16 queries. Numeric scale and similar overall
accuracy did not make their rankings interchangeable in this fixture. This is
not a general claim about model specialization.

This study does not implement a selector/interpreter factorial. It does not
test whether using the same model for selection and interpretation changes
correlated error relative to cross-model use. That hypothesis remains open.

## 5. Evidence classification and interpretation

### Established in this repository

- The preserved one-bug, multi-bug, VOI, and policy artifacts retain their
  stated provenance and limits in Sections 1 and 2.
- The model-role raw files reproduce the frozen point metrics and bootstrap
  intervals. Both run files are byte-identical, with no invalid model outputs.
- In this synthetic relevance fixture, similarity, model confidence, and
  binary critic outputs have different calibration and ranking behavior.
- An equal-weight calibrated judge pool can improve accuracy while worsening
  proper scoring rules compared with one judge.

### Supported by primary documentation

Google's [EmbeddingGemma 2 model card](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2)
documents SentenceTransformers use, retrieval prefixes, 768-dimensional
embeddings, and float32 use on most CPUs. Ollama's [MLX announcement](https://ollama.com/blog/mlx)
documents an Apple Silicon runtime. Neither source verifies the requested
Ollama tag on this Linux host or makes two packaging paths equivalent.

### New experimental findings

- Tev1 reached perfect accuracy and AUC on these small authored family-specific
  sets. The binary target has ECE 0.0681; common-target software relevance has
  Brier 0.2166, versus 0.0047–0.0097 in its other relevance domains.
- EmbeddingGemma's held-out raw-score AUC ranges from 0.2471 to 0.9823 across
  the four domains. A global calibration map does not make its scores behave
  like the other roles' probabilities.
- Qwen, Gemma, and Guardian have observed disagreement but no joint error in
  512 held-out items. This sample cannot establish independent errors.
- Coder and Gemma disagree on the top safety item in 11 of 16 queries despite
  equal mean accuracy. The probability pool also has worse proper scores than
  Qwen alone.
- Exact replay succeeded for the same frozen inputs. It does not demonstrate
  generalization or independent replication on a new sample.

### Remaining hypotheses

- Calibration may transfer to other tasks within or across these role types.
- A model's identity, training lineage, or shared encoder may predict judgment
  dependence outside these authored rows.
- A retrieval score may become useful as a calibrated probability under a
  different target and independent sampling process.
- Same-model and cross-model selector/interpreter combinations may differ in
  correlated errors or task outcomes.
- A runtime rule for operation-specific commensurability may outperform
  simpler rules after independent review and testing on corrected cases.

## 6. Prospective work

Keep v2.3 and both runs frozen. Do not tune this protocol using its outcomes.

1. Build a new, predeclared case set with independent labels and held-out
   questions from multiple domains. Keep each target and estimand explicit.
2. Test within-target and cross-family calibration transfer on new cases. Do
   not pool probability vectors with different outcome definitions.
3. Run a selector/interpreter factorial with same-model and cross-model pairs.
   Preserve per-case outputs and compare correlated errors before aggregate
   task success.
4. Test a second EmbeddingGemma backend only as a separately named condition.
   Compare exact weights, tokenizer, prefixes, normalization, numerical output,
   and host before making any parity claim.
5. Obtain an independent human review of the operation-policy challenge. Keep
   v2 unchanged; resolve calibration provenance, labels, and threshold
   reference before scoring any corrected v3 cases.

## Delivery and remaining gates

PR #54 remains a draft. Do not split it: retrieval, policy, and model-role
changes share the research record and their commit history is interleaved.
The runtime checkpoint is commit
[`e254ba0`](https://github.com/AbstractLogix/isoprax/commit/e254ba0476085cf75bf21f0c1aceaa4d9b954862).
Its local hooks and hosted CI passed. No independent human reviewer is
available on the repository at this time.

Keep the v3 policy inputs unscored until their labels, calibration provenance,
and threshold reference are resolved. The model-role experiment does not
independently validate the operation-specific policy. Do not send a rule to
Semadmit from this synthetic or internally authored evidence. Keep the Haskell
oracle limited to checking IsoPrax's public semantics.

**Model-role status:** `MODEL-ROLE FINDINGS REPRODUCED`.

**Independent review status:** `INDEPENDENT OPERATION-SPECIFIC VALIDATION NOT YET SUPPORTED`.

**Semadmit status:** `NO SEMADMIT RULE WARRANTED`.
