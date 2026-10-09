# Paper replication and integrity record

## Reproduction command

From the repository root:

```sh
uv run python scripts/paper_integrity.py
uv run pytest --no-cov tests/test_paper_integrity.py
```

The first command checks [`paper-integrity-lock.json`](paper-integrity-lock.json), source and package hashes, raw run structure, frozen replay identity, registered artifact digests, numeric paper claim tags, and deterministic repository experiments. It writes [`paper-recomputed-results.json`](paper-recomputed-results.json), which preserves per-run outcome rows for the raw retrieval and acquisition experiments and computed case-level metrics for the model-role experiment. It makes no network calls or model calls.

## Pinned raw sources

The Bouleusis source records are from private repository commit `9f239d6f59cd22e1c1ebf1b9d86b0f28a8fc45b5`. The packaged gzip files decompress to the exact original JSONL bytes and hashes. The raw records are not edited. The source repository metadata reports `NOASSERTION`; the owner separately authorized public release of the four exact files listed in the manifest under CC BY 4.0. This authorization does not cover Bouleusis source code or third-party material. See the [release scope and rights audit](publication-rights-audit-2026-10-09.md). The private source may still require authenticated access for a reviewer of provenance.

The model-role v2.3 source includes two preserved raw JSON files and multipart gzip archives. Each archive reconstructs to the matching raw JSON digest. The two raw runs are byte-identical. The v2.3 case/prompt/model bytes were hashed before scored calls, but the Git commit was made after Run 1 began. This historical ordering is retained.

## Evidence classes

- **Established repository results:** IsoPrax checks structured outcome and operation declarations. The deterministic fixtures reproduce their registered outputs. The checker does not establish that declarations match real measurement pipelines.
- **Literature-supported statements:** Calibration and proper scoring are target-relative, and forecast combination has an established literature. See [Gneiting and Raftery](https://doi.org/10.1198/016214506000001437), [Guo et al.](https://proceedings.mlr.press/v70/guo17a.html), and [Bates and Granger](https://doi.org/10.1057/jors.1969.103). These works do not establish equivalence between the IsoPrax targets.
- **New experimental findings:** Benchmark A, the authored operation-rule challenges, and the raw Bouleusis/model-role recomputations provide finite synthetic or source-specific results, with their exact limits reported below.
- **Remaining hypotheses:** Operation-specific gating will generalize; declarations can be validated against real observation processes; and any model or judge combination has useful behavior beyond the declared mixture. These need independent cases, reference outcomes, and review.

## Recomputed findings

Values below are generated from raw records by the command above. `paper-recomputed-results.json` is the authoritative table and retains each run-level outcome. Summaries in this report do not replace the row-level data.

### One-bug retrieval sweep

The raw input has 170 runs: four bounded selectors at each of four bounded budget settings, ten order perturbations per arm/budget, plus the separate full-context reference with ten order perturbations. Full context is not a bounded arm. The exact per-run selection, recall, success, and epistemic data remain in the recomputed JSON.

The matched 540-byte comparison has only Random, Lexical, EmbeddingGemma 2, and the fixture-order positive control. The full-context reference is unbounded and uses 660 bytes. Random retains decisive evidence across all order perturbations but succeeds on only half. The lexical and embedding arms abstain on the same fixture and do not retain decisive evidence at this budget. The positive control succeeds on each order perturbation. These are ten repeated orders of one bug, not ten independent tasks. Complete evidence availability converges all selector arms on successful debugging. Full context achieves repair while residual false-belief mass remains in its event log; this does not establish that complete context causes false beliefs or is epistemically worse.

| Condition | Budget | Decisive-evidence recall | Debugging success | Abstention |
|---|---|---:|---:|---:|
| Random | 540 bytes | 10/10 | 5/10 | 0/10 |
| Lexical | 540 bytes | 0/10 | 0/10 | 10/10 |
| EmbeddingGemma 2 | 540 bytes | 0/10 | 0/10 | 10/10 |
| Fixture-order positive control | 540 bytes | 10/10 | 10/10 | 0/10 |
| Full-context reference | Unbounded, 660 bytes | 10/10 | 10/10 | 0/10 |

The full-context event log has mean false-belief confidence mass 0.166667 across the order trials. This records epistemic residue alongside successful repair. It does not explain why residual mass remained or establish that one retrieval mode caused it.

**Source-record discrepancy:** The supplied summary placed full context alongside the 540-byte condition. The raw JSONL records identify full context as unbounded and show 660 bytes. This is a summary-labeling discrepancy, not corruption of the raw records. The reanalysis follows the raw records; no raw record is rewritten to match the earlier summary.

### Multi-bug retrieval

The raw input has 228 run rows over 12 fixed cases. Six bounded arms are crossed with three budgets, with 12 cases per cell; full context is a separate unbounded reference. The report preserves success, selected bytes, decisive-evidence recall, and false-belief mass for every case/run. All bounded all-evidence conditions and full context converge to successful debugging on the fixed cases. The raw epistemic field reports zero false-belief confidence mass in the multi-bug records. Case count does not make repeated conditions independent samples.

### Acquisition and value of information

The raw input has 144 rows: six policies by 12 cases by two budgets. The deterministic value-of-information policy chooses the same acquisition action as always-retrieve on all 24 case/budget states. At the tight budget, both have zero successes among 12 cases, mean 184.17 acquired bytes, and 12 unnecessary acquisitions. At the medium budget, both succeed in 12 of 12 cases, average 256 bytes, and zero unnecessary acquisitions. No superiority is established. The oracle is a non-deployable control.

The separate acquisition audit contains 543 records. Decision-change probability and abstention-resolution probability are explicitly unmodeled in these records. They remain unavailable; the analysis does not infer them from a Markdown report. See the generated `unavailable_from_raw_records` list.

### Model-role results

Each raw run contains 192 Tev1 rows, 6,144 relevance rows, and 960 captured raw responses. Both runs have matching raw digests. The verifier recomputes per-family Tev1 calibration and proper scores; per-model, per-domain held-out performance; case/query-cluster bootstrap intervals; ranking behavior; paired judge disagreements and joint errors; equal-weight probability pool metrics under the declared common relevance target; and coding-specialist top-item disagreements. Invalid rows and their denominators are retained.

The equal-weight model pool is only interpreted for the explicitly declared equal-weight mixture over four authored relevance domains, and it also names its equal model weights. The Tev1 equal-family summary is interpreted as an expected metric after sampling one of its three authored families uniformly. Neither mixture implies target equivalence outside those specified mixtures.

Zero joint errors across held-out examples are a count for these records. The query bootstrap percentile interval collapses to zero because each observed query has zero joint errors; it is not a bound on unseen-task risk and does not establish independence. Exact byte replay shows repeatability on these inputs, not replication across new tasks, labels, prompts, runtimes, hosts, or model versions.

### Model-role held-out results

All Tev1 rows below are from the held-out split. Each family has 32 cases. All rows are valid. The bootstrap resamples cases. The table reports accuracy, multiclass Brier score, log loss, expected calibration error (ECE), and macro one-vs-rest AUC.

| Tev1 family | Class counts | Accuracy | Brier | Log loss | ECE | Macro AUC | 95% CI: Brier; log loss; AUC |
|---|---|---:|---:|---:|---:|---:|---|
| Equipment binary | false 16, true 16 | 1.000 | 0.010441 | 0.070880 | 0.068114 | 1.000 | [0.008126, 0.012648]; [0.062011, 0.079397]; [1, 1] |
| Incident ordinal | critical 8, limited 8, major 8, routine 8 | 1.000 | 0.000001009 | 0.000768 | 0.000768 | 1.000 | [0.000000775, 0.000001260]; [0.000682, 0.000858]; [1, 1] |
| Software category | bad serialization 8, null dereference 8, race condition 8, stale cache 8 | 1.000 | 0.000002432 | 0.001189 | 0.001189 | 1.000 | [0.000001954, 0.000002917]; [0.001030, 0.001330]; [1, 1] |

The declared equal-family estimand is the expected log loss after sampling one of these three authored families with weight 1/3. Its recomputed value is 0.024279 (case-bootstrap 95% CI [0.021474, 0.027337]). This is an average of family-specific losses, not a pool of probabilities across different label spaces. Perfect held-out discrimination in these small authored cases does not establish natural question-family calibration.

For relevance scoring, every model-by-domain cell has 128 held-out items (48 positive, event rate 0.375), 16 held-out queries, and zero invalid outputs. Platt calibration is fit on that domain's development records; held-out records are used only for evaluation. The table shows native-score AUC, calibrated Brier/log loss/AUC/ECE, and raw-score ranking MRR/recall at 3. Values are rounded to three decimals. Full-precision estimates and query-cluster 95% intervals for Brier, log loss, AUC, MRR, and recall are in the machine-readable results.

| Model role | Domain | Native AUC | Brier | Log loss | Calibrated AUC | ECE | MRR / Recall@3 |
|---|---|---:|---:|---:|---:|---:|---:|
| Coder | Equipment | 1.000 | 0.037 | 0.142 | 1.000 | 0.131 | 1.000 / 1.000 |
| Coder | Policy | 1.000 | 0.037 | 0.140 | 1.000 | 0.130 | 1.000 / 1.000 |
| Coder | Safety | 1.000 | 0.037 | 0.142 | 1.000 | 0.132 | 1.000 / 1.000 |
| Coder | Software | 1.000 | 0.038 | 0.143 | 1.000 | 0.132 | 1.000 / 1.000 |
| Embedding | Equipment | 0.805 | 0.465 | 0.657 | 0.805 | 0.007 | 1.000 / 0.667 |
| Embedding | Policy | 0.364 | 0.468 | 0.661 | 0.636 | 0.002 | 0.388 / 0.250 |
| Embedding | Safety | 0.247 | 0.466 | 0.659 | 0.753 | 0.000 | 0.242 / 0.063 |
| Embedding | Software | 0.982 | 0.468 | 0.661 | 0.982 | 0.005 | 1.000 / 0.979 |
| Gemma | Equipment | 0.917 | 0.219 | 0.370 | 0.917 | 0.156 | 1.000 / 0.833 |
| Gemma | Policy | 1.000 | 0.072 | 0.196 | 1.000 | 0.174 | 1.000 / 1.000 |
| Gemma | Safety | 1.000 | 0.073 | 0.192 | 1.000 | 0.170 | 1.000 / 1.000 |
| Gemma | Software | 1.000 | 0.100 | 0.232 | 1.000 | 0.190 | 1.000 / 1.000 |
| Guardian | Equipment | 0.500 | 0.469 | 0.662 | 0.500 | 0.004 | 1.000 / 0.667 |
| Guardian | Policy | 0.500 | 0.469 | 0.662 | 0.500 | 0.004 | 1.000 / 0.667 |
| Guardian | Safety | 0.500 | 0.469 | 0.662 | 0.500 | 0.004 | 1.000 / 0.667 |
| Guardian | Software | 0.500 | 0.469 | 0.662 | 0.500 | 0.004 | 1.000 / 0.667 |
| Qwen | Equipment | 1.000 | 0.026 | 0.111 | 1.000 | 0.103 | 1.000 / 1.000 |
| Qwen | Policy | 1.000 | 0.020 | 0.103 | 1.000 | 0.098 | 1.000 / 1.000 |
| Qwen | Safety | 0.996 | 0.074 | 0.171 | 0.996 | 0.076 | 1.000 / 1.000 |
| Qwen | Software | 1.000 | 0.020 | 0.105 | 1.000 | 0.099 | 1.000 / 1.000 |
| Tev1 | Equipment | 1.000 | 0.025 | 0.116 | 1.000 | 0.109 | 1.000 / 1.000 |
| Tev1 | Policy | 1.000 | 0.037 | 0.140 | 1.000 | 0.130 | 1.000 / 1.000 |
| Tev1 | Safety | 1.000 | 0.023 | 0.112 | 1.000 | 0.105 | 1.000 / 1.000 |
| Tev1 | Software | 0.974 | 0.247 | 0.415 | 0.974 | 0.218 | 1.000 / 0.958 |

Native scores remain different objects: model-reported probabilities, embedding cosine values, Tev1 outputs, and Guardian's binary judgments. Their common numeric representation does not make the native scores interchangeable. EmbeddingGemma's native AUC ranges from 0.247 to 0.982 by domain; Guardian's is 0.500 in each domain. A low ECE after calibration does not erase the large Brier/log-loss differences. The per-domain results do not support treating retrieval similarity as model confidence or as critic confidence.

The declared judge probability mixture uses the common authored relevance target, weights each of Qwen, Gemma, and Guardian at 1/3, and samples each of the four domains with weight 1/4. For that estimand, the pool has accuracy 1.000, AUC 1.000, Brier 0.103582 (95% CI [0.095703, 0.112246]), and log loss 0.247340 (95% CI [0.237626, 0.258619]). Qwen alone on the same declared domain mixture has accuracy 0.986328, AUC 0.999089, Brier 0.020728, and log loss 0.063376. The pool raises threshold accuracy in these records and has worse proper scores. It is not evidence for cross-family outcome pooling.

The verifier preserves per-item and per-query judge comparisons. Across each pair, there are 512 paired held-out items in 64 queries and zero joint observed errors; the query-cluster interval is [0, 0]. Qwen/Gemma disagree on 8 labels, with 7 Qwen errors and 1 Gemma error; Qwen/Guardian disagree on 199 labels, with 7 Qwen errors and 192 Guardian errors; Gemma/Guardian disagree on 193 labels, with 1 Gemma error and 192 Guardian errors. These counts show that judge behavior differs on this set. They do not estimate population independence. For top-item selection, Coder and Qwen agree on all 64 queries. Coder and Gemma disagree on 11/64, all 11 within the 16 safety queries. Per-query item IDs and labels are retained in the JSON.

## Other deterministic checks

The command re-runs Feature 046's synthetic Benchmark A and operation gate and compares canonical results to the committed JSON. It independently reduces false permissions, unnecessary refusals, and interpretation errors from the saved 23 case rows. The operation-specific rule has zero on these three measures in that authored challenge; simpler rules have false permissions. Ranking-change and decision-change totals also match when the deterministic runner executes, but those per-case outputs are absent from the saved case rows and cannot be independently reduced from them. The set is not representative and the labels were not independently adjudicated. The result is descriptive and does not prove independent value.

The operation-policy v2 challenge remains distinct. It is an internally authored frozen case set. Four forecast calibration-revision cases remain excluded from positive policy-validity claims. No Semadmit operational rule is derived from these results.

The integrity command reduces every v2 policy/operation summary from the 36 saved per-case outputs and checks it against the frozen aggregate. It reports false permissions, unnecessary refusals, interpretation errors, ranking changes, and decision changes. The four calibration-revision mismatch cases remain unresolved and excluded from positive policy-validity claims until valid reference evidence exists.

The table below reports the independently reduced v2 rows. Each operation has 12 cases, with six evaluator-labeled valid and six invalid. `D` and `R` show decision and ranking interpretation errors among cases with both an expected and produced result. `Δ` is the number of decisions or rankings changed from naive aggregation among cases with an explicit estimand. The forecast-pool counts include FP02, FP03, FP05, and FP06 for descriptive completeness; none of those four supports a positive policy-validity claim.

| Operation | Rule | False permissions | Unnecessary refusals | Interpretation errors | Changes vs naive |
|---|---|---:|---:|---|---|
| Evidence combine | Naive aggregation | 6/6 | 0/6 | — | — |
| Evidence combine | Global label | 6/6 | 1/6 | — | — |
| Evidence combine | Metadata-only | 1/6 | 5/6 | — | — |
| Evidence combine | Operation-specific | 0/6 | 0/6 | — | — |
| Forecast pool | Naive aggregation | 6/6 | 0/6 | D 2/9 | D 0/9 |
| Forecast pool | Global label | 5/6 | 0/6 | D 2/8 | D 1/9 |
| Forecast pool | Metadata-only | 2/6 | 5/6 | D 1/3 | D 6/9 |
| Forecast pool | Operation-specific | 0/6 | 4/6 | D 0/2 | D 7/9 |
| Relevance rank | Naive aggregation | 6/6 | 0/6 | R 2/10 | R 0/12 |
| Relevance rank | Global label | 6/6 | 2/6 | R 2/8 | R 2/12 |
| Relevance rank | Metadata-only | 3/6 | 5/6 | R 0/4 | R 8/12 |
| Relevance rank | Operation-specific | 0/6 | 0/6 | R 0/6 | R 8/12 |

On these cases, operation-specific checks reduce false permissions. They also refuse four of six valid forecast-pool cases. Metadata-only reaches zero ranking interpretation errors on the four cases where it emits a ranking, but refuses five of six valid relevance-rank cases. The denominators matter: these are not matched accuracy estimates, and the evaluator labels are internally authored. The results do not settle whether the extra rule complexity is useful on independently authored cases.

## Hypothesis status and answers

- **Operation-specific gating:** It showed a measurable advantage on the fixed, internally authored 23-case challenge: zero listed errors versus false permissions and other errors for simpler rules. This does not establish advantage on unseen or field cases. The rule has not earned operational complexity beyond that fixture.
- **Shared model identity:** No experiment shows that identity alone justifies cross-family pooling. The shared model-role study concerns synthetic task families and does not define a common JIT/AIOps event.
- **Evidence-presence sufficiency:** Weakened by the one-bug counterexample. Random selection included decisive evidence in every order trial but succeeded in only half. The records do not isolate a causal explanation among composition, order, interpretation, and downstream repair.
- **Accuracy as a complete pooling criterion:** Weakened in the fixed model-role relevance target. The probability pool increased threshold accuracy while worsening Brier and log loss relative to a component model.
- **Model diversity implies independent evidence:** Not supported. The fixed judge case set had zero observed joint errors, but that is insufficient to establish independence or population risk.
- **VOI beats always-retrieve:** Not supported on the 24 controlled case-budget states; both policies select the same actions and have matching outcomes within each budget.
- **Semantic truth from structured equality:** Not established. The code compares declarations; the evidence does not show that equal declarations guarantee equal real-world observation pipelines.

No new Semadmit operational rule is mature for deployment. Matching structured declarations and operation-specific metadata can remain a candidate test contract, but any operational use needs independent reference outcomes, declaration-quality checks, and prospective validation. The current evidence is not sufficient to send a rule to Semadmit.

## Next experiment

Preregister a blinded, independently authored multi-case conformance study before scoring. Vary one target field at a time and include both the deceptive-equal-metadata false-permission case and a semantically equivalent, differently worded positive case. Have a separate reviewer adjudicate target and operation ground truth. Freeze case text, metadata, reference outcomes, simple baselines, decisions, and analysis before the candidate implementation is run. Report per-case false permissions, unnecessary refusals, interpretation errors, rank changes, and decision changes. Treat cases as the sampling unit; do not use repeats of one bug or one query as independent tasks.

## Method and interpretation limits

- Probability and ranking metrics are recomputed from raw predictions and labels. Calibration is fitted on development rows only. Held-out rows are used only for metrics.
- Bootstrap resampling uses cases for Tev1 and query clusters for relevance, ranking, and paired judgment errors. The fixed query sets are synthetic; interval width does not repair construct or sampling limitations.
- The designated probability pools use only explicit equal-weight estimands over named synthetic targets. We do not pool model scores merely because their data type is numeric.
- A hash verifies byte identity, not source truth, access rights, calibration, construct validity, or independence.
- No external scientific review has occurred. Reproduction is not independent peer review.

## Verification record

The integrity runner passed with 36 registered claims, 17 numeric manuscript lines, 170 one-bug records, 228 multi-bug records, 144 acquisition records, and byte-identical model-role archives. It regenerated the machine-readable results and quantitative tables from pinned inputs.

- `uv run pytest --no-cov tests/test_paper_integrity.py` — PASS, 16 tests.
- `uv run ruff check scripts/paper_integrity.py tests/test_paper_integrity.py` — PASS.
- `uv run ruff format --check scripts/paper_integrity.py tests/test_paper_integrity.py` — PASS.
- `python3 /mnt/c/Users/abstr/.codex/cheap-context-workflow/verify_generated.py --command "uv run pytest --no-cov tests/test_paper_integrity.py"` — PASS.
- The repository pre-commit suite ran 649 tests successfully with 4 skips, but its coverage gate failed at 94.33% against a 95% minimum. The report attributes 239 missed statements to `isoprax/eb_jepa.py` (30% coverage); the publication branch does not change `isoprax/` relative to its PR #54 base. This repository-wide coverage gate remains open.
- The complete CLI rejected three temporary mutations: a changed manuscript number, changed raw artifact bytes, and a changed recorded artifact digest.

These checks establish mechanical integrity for the exact pinned package. They do not establish construct validity, field performance, independent review, or generalization to new tasks. The clean-checkout rerun is recorded in [publication readiness](publication-readiness-2026-10-09.md) after the publication commit is created.
