# Experimental Evidence: Commensurability and Shared Model Identity

**Run date**: 2026-10-05
**Status**: Executed deterministic synthetic experiments
**Machine-readable output**: [experimental-results.json](experimental-results.json)

Reproduce the run from the repository root:

```bash
uv run python -m isoprax.research_experiments --output docs/research/experimental-results.json
```

The runner uses seed `4605`, one fitted CPU JEPA reference backend, target-local isotonic calibration, and 500 bootstrap resamples for each shared-model target and its same-target pool. Each interval records its target-specific seed. The runner has no network access. The bootstrap intervals describe sampling variation conditional on the synthetic generator. They do not include generator, model, or real-world uncertainty.

## Evidence classes

### Established in this repository

- `OutcomeDefinition` records an event, observation process, window, and thresholds. The existing commensurability check rejects event or observation-process differences. The check is a bounded reference rule; it does not assess every operation.
- Calibration measures are relative to declared scores and outcomes. The existing `evidence.py` fixture also shows how locally calibrated 7-day and 90-day targets can yield a changed pooled selection. Those windows remain different targets.
- The deterministic JEPA reference emits Change risk and Operational anomaly readouts from one backend identity. The existing implementation already states that model identity and calibration do not establish shared outcome semantics.
- The Haskell semantic oracle remains a small independent differential check of public semantics. This phase did not add trust, runtime admission, or enforcement behavior to it.

### Supported by primary literature

- Forecast verification and proper scoring rules evaluate forecasts against their stated outcomes. They do not prove that different outcomes describe the same event. See [Gneiting, Balabdaoui, and Raftery (2007)](https://doi.org/10.1111/j.1467-9868.2007.00587.x) and [Gneiting and Raftery (2007)](https://doi.org/10.1198/016214506000001437).
- Multicalibration addresses calibration across specified subgroups. It does not establish equivalence between different outcome definitions. See [Hébert-Johnson et al. (2018)](https://proceedings.mlr.press/v80/hebert-johnson18a.html).
- Measurement invariance, dataset-shift evaluation, and dependence-aware evidence combination provide bounded methods for their stated settings. They do not prove that one operation table applies to every machine-generated evidence type. See [Sterner et al. (2024)](https://doi.org/10.1080/10705511.2024.2339396), [Ovadia et al. (2019)](https://proceedings.neurips.cc/paper_files/paper/2019/hash/8558cb408c1d76621371888657d2eb1d-Abstract.html), and [Shafer (2016)](https://doi.org/10.1016/j.ijar.2016.05.003).

These sources motivate the tests. They do not validate the new IsoPrax gate or synthetic results.

### New experimental findings

All results in this section are synthetic. They do not establish real-world predictive efficacy, Semantic or Full Conformance, or operational validity.

#### Invalid-Aggregation Benchmark A

Each different-target lane has 100 records. Every forecast is `0.80`; each lane has 80 positive outcomes and 20 negative outcomes. The Change lane measures a fix-linked defect within 30 days through repository fix-link observation. The Operational lane measures a telemetry threshold breach within 30 minutes through deployment telemetry.

| Lane | Mean forecast | Event rate | ECE, 10 equal-width bins | Brier score | AUC |
|---|---:|---:|---:|---:|---:|
| Change, 30-day fix-link event | 0.80 | 0.80 | 0.00 | 0.16 | Not meaningful: constant forecasts |
| Operational, 30-minute threshold event | 0.80 | 0.80 | 0.00 | 0.16 | Not meaningful: constant forecasts |

The runner also reports a pooled numeric value of `0.80` for target `synthetic.mixture.change-30d-and-operational-30m.equal-weight`. Its exact estimand selects the Change or Operational lane with probability `0.50` each, then observes that selected lane's own event. The weights are `{change: 0.50, operational: 0.50}`. This is an equal-weight mean of two event risks. It is not the risk of one common event. The 200-row mixture has event rate `0.80`, ECE `0.00`, and Brier score `0.16`.

The valid control uses the same service threshold event, observation process, 30-minute window, and threshold in both 100-row lanes. Under the predeclared 50:50 cohort mixture, it has mean forecast `0.80`, event rate `0.80`, ECE `0.00`, and Brier score `0.16` for that one named target.

Permitted operations are target-local calibration reports and the exact declared mixture report. The same-target control also permits its named common-target pool. The benchmark prohibits interpreting equal probabilities, equal calibration, or the different-target `0.80` mixture as proof of one common event.

#### Shared-model experiment

One deterministic JEPA backend identity (`b3856d06…`) supplies all Change and Operational readouts. Each target has an independent 240-row calibration split and 300-row test split. The outcomes are generated from the synthetic scores and fixed random seeds. They are deliberately useful for exercising target separation; they are not external labels or evidence of predictive efficacy.

The repository's current definition check marks the different-family pair `irreducible`, the horizon pair `bridgeable` but not poolable, and the same-target control `direct`. The check and the experiment agree that a shared backend ID does not change the target relation.

The table reports event rate, ten-bin ECE, Brier score, ROC AUC, bootstrap intervals, and target-local top-20% selection. Intervals are 95% percentile bootstrap intervals from 500 resamples.

| Target and cohort | Calibration / test n | Positive / negative | Event rate (95% CI) | ECE (95% CI) | Brier (95% CI) | ROC AUC (95% CI) | Top 20% selected |
|---|---:|---:|---:|---:|---:|---:|---:|
| Change fix-link event, 30 days | 240 / 300 | 144 / 156 | 0.480 (0.427–0.537) | 0.069 (0.055–0.144) | 0.238 (0.217–0.261) | 0.643 (0.579–0.702) | 44/60 positive; 0.733 selected rate |
| Operational threshold event, 1 hour | 240 / 300 | 123 / 177 | 0.410 (0.363–0.468) | 0.037 (0.013–0.089) | 0.231 (0.222–0.241) | 0.625 (0.563–0.683) | 30/60 positive; 0.500 selected rate |
| Operational threshold event, 24 hours | 240 / 300 | 168 / 132 | 0.560 (0.507–0.613) | 0.060 (0.023–0.116) | 0.226 (0.215–0.237) | 0.655 (0.594–0.711) | 43/60 positive; 0.717 selected rate |
| Same 1-hour target, control cohort A | 240 / 300 | 122 / 178 | 0.407 (0.347–0.465) | 0.110 (0.062–0.166) | 0.240 (0.232–0.248) | 0.660 (0.605–0.717) | 32/60 positive; 0.533 selected rate |
| Same 1-hour target, control cohort B | 240 / 300 | 136 / 164 | 0.453 (0.395–0.510) | 0.040 (0.022–0.102) | 0.234 (0.222–0.246) | 0.622 (0.562–0.682) | 33/60 positive; 0.550 selected rate |

The 1-hour and 24-hour cases reuse 300 paired synthetic observations. All 123 one-hour positive labels are also positive at 24 hours; the 24-hour case has 168 positives. The different windows remain different targets. No family or horizon metrics are pooled.

The same-target positive control declares this exact estimand before pooling: calibration and forecast error for `synthetic.operational.failure.1h` in an equally weighted 50:50 mixture of synthetic cohorts A and B. The pool has `n=600`, 258 positives, event rate `0.430` (95% CI `0.392–0.473`), ECE `0.073` (95% CI `0.044–0.118`), Brier score `0.237` (95% CI `0.230–0.245`), and AUC `0.635` (95% CI `0.590–0.675`).

The diagnostic global top-20% ranking selects 112 Change and 8 Operational records in the different-family case. It selects 23 one-hour and 97 24-hour records in the different-horizon case. These cross-target rankings are explicitly diagnostic and unsupported as common-risk rankings. The same-target control permits ranking for its declared target.

#### Operation-gate comparison

The fixed challenge set has 23 authored cases: 12 invalid and 11 valid requested operations. The declared decision rule reviews the global top 20% only when the requested ranking is valid; otherwise it reviews the top 20% within each target. Decision changes count record-selection differences from each case's predeclared valid action.

| Rule | False permission | Unnecessary refusal | Interpretation errors | Ranking cases changed | Selected-record decisions changed |
|---|---:|---:|---:|---:|---:|
| Naive aggregation | 12/12 | 0/11 | 8/23 | 2/4 | 8 |
| One global commensurability label | 7/12 | 3/11 | 3/23 | 1/4 | 4 |
| Metadata-only rule | 5/12 | 0/11 | 0/23 | 1/4 | 4 |
| Operation-specific rule | 0/12 | 0/11 | 0/23 | 0/4 | 0 |

The operation-specific rule adds measurable value on this challenge set. It prevents five false permissions made by the metadata-only rule and avoids four selected-record changes. It also matches the metadata-only rule on unnecessary refusals and interpretation counts. The cases were authored from the proposed operation conditions, so the zero-error result is partly built into the challenge design. These counts are not independent review, field error rates, or proof of lower production decision loss.

## Answers to the requested questions

### 1. Did operation-specific commensurability provide measurable value beyond simpler rules?

Yes, on this fixed synthetic challenge set: the operation-specific rule had 0/12 false permissions versus 5/12 for metadata-only, with the same 0/11 unnecessary refusals and 0/23 interpretation errors. It changed no selected-record decisions, compared with four changes for metadata-only. This supports further study. It does not establish value on external or operational cases.

### 2. Did shared model identity ever justify cross-family pooling by itself?

No. The same backend identity appears on different-family and different-horizon outputs, but their pooled metrics are withheld. The experiment permits a pool only for the same one-hour target with an explicit 50:50 cohort estimand and weights. Model identity alone does not establish semantic equivalence.

### 3. Which IsoPrax rules are mature enough to propose for Semadmit operationalization?

The bounded rules with repository implementation and focused evidence are the best candidates for Semadmit to review: retain explicit event, observation-process, window, and threshold fields; keep target commensurability separate from calibration; preserve per-target metrics; and require an exact declared estimand and weights before reporting a pool. The current public check remains limited to its documented fields. The new operation-specific table is not mature enough to present as a complete enforcement policy. Semadmit owns runtime admission and verification enforcement; this report does not implement it.

### 4. Which hypotheses were weakened or falsified?

- The claim that shared model identity is sufficient for cross-target comparison or pooling is contradicted by the different-family and different-horizon cases in this synthetic run.
- The claim that a metadata-only rule is sufficient for every operation is weakened by five false permissions in the authored case set.
- The operation-specific proposal gained a challenge-set advantage, but its general value remains unproven because the cases were authored from that proposal.
- The experiment does not test whether cross-family aggregation can be useful under a rigorous shared estimand. Benchmark A shows that a named risk mixture can be reported without claiming one common event.

### 5. What should IsoPrax test next?

Use independent case authors and reviewers to build a preregistered operation set. Test agreement and error rates on public, provenance-backed data with shared system lineage where possible. Include population shift, model-version change, sample overlap, and dependence cases. Compare target-only metadata against operation-specific checks under held-out cases and a named decision rule. Keep each target and source separate unless a common estimand is declared before analysis.

## Remaining hypotheses

- Operation-specific checks improve real comparison or decision quality over simpler metadata on independent benchmarks.
- Reviewers can apply the candidate operation conditions with acceptable agreement.
- Explicit mixture estimands remain useful and stable under changed populations and weights.
- Public data can support shared-target claims when its lineage and observation process justify them.

Negative or equivalent results on independent cases should narrow the proposal. They should not trigger a larger framework by default.

## Validation performed

- The final result file was generated twice by the documented runner. Both files had SHA-256 `02d3642044768c47957221a1e615dc221baf248b97eb4a61c8d75fa8eca80fcd`.
- Focused research, JEPA, and Haskell-oracle tests passed: 42 passed and one skipped in the combined run. The Haskell test passed separately when pointed at the locally built oracle binary.
- The bounded Haskell oracle passed its offline Cabal build, six QuickCheck properties with 2,000 cases each, compile-fail check, and Python differential test. No Haskell source changed in this phase.
- Repository-wide Ruff lint and format checks passed. All test assertions in the full Python suite passed: 594 passed and 4 skipped. The experiment runner measured 99% branch-aware coverage and the operation-gate module measured 100% in that run.
- The pre-commit syntax, JSON, whitespace, and Ruff hooks passed. Its contract-test hook reported the repository-wide coverage shortfall listed below.
- Local repository-wide coverage was 94.33%, below the configured 95% threshold. This environment does not include the optional GPU extra, so the EB-JEPA module tests were skipped. The CI workflow installs that extra; hosted coverage remains to be confirmed by the PR checks.
- `git diff --check` passed. The separate Feature 044 qualification worktree remains unchanged by this phase.

The local aggregate coverage result is an environment limitation, not evidence that the hosted gate passed. Do not treat the phase as merge-ready until the required PR checks report their results.
