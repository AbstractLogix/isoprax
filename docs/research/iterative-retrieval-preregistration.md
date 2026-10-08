# Prospective Iterative Retrieval Preregistration

**Status**: Prospective preregistration; analysis and decision margins are
declared, but the exact task IDs, model revisions, and run configuration must
be frozen before execution.
**Owner boundary**: IsoPrax defines measures and analysis. Bouleusis owns
deliberation and retrieval behavior.

This protocol tests whether a second retrieval round improves investigation
outcomes. It does not specify or implement Bouleusis behavior. Freeze the task
set, model revisions, prompts, budgets, and analysis before scored runs.

## Research question and hypotheses

**Question**: At a fixed evidence-byte budget, does
`retrieve → reason → identify missing information → retrieve again → reason`
improve verified task success over a one-round retrieval path?

- **H1, primary**: Two-round retrieval improves final verified task success
  over a same-selector one-round run at the same cumulative evidence-byte
  budget.
- **H2**: New retrieval evidence adds value beyond a second reasoning pass that
  receives no new evidence.
- **H3**: Iteration recovers a measurable share of first-round failures.
- **H4**: Any success gain does not come with an unacceptable increase in false
  repairs, unnecessary re-retrieval, or false-hypothesis confidence mass.

These hypotheses concern the tested tasks and budget. They do not establish
that iterative retrieval is necessary in general.

## Sample and experimental unit

- Use at least 20 independent bugs, with at least five bugs in each of four
  predeclared root-cause or evidence-shape strata.
- Count a bug as independent only if it has a distinct injected root cause and
  is not a near-duplicate of another bug. Rewordings, order permutations,
  hypothesis-ID changes, and random seeds for the same defect are repeated
  measures within that bug.
- Run five paired seeds per bug and condition. Apply the same seed schedule to
  each paired condition. Seeds estimate repeatability within a bug; the bug is
  the unit for the primary inference.
- Before scored runs, freeze each bug, repository state, hidden and visible
  tests, evidence set, evidence labels, candidate hypotheses, and expected
  repair. Have reviewers who do not see selector outputs label evidence
  relevance, decisive status, sufficiency, and contradictions.
- If fewer than 20 independent bugs pass review, report a pilot. Do not claim a
  multi-bug population result.

Twenty bugs is a proposed minimum panel, not a universal sample-size threshold.
Run a power or precision analysis using independent-bug variation before
increasing the sample or making subgroup claims.

## Conditions

Run paired conditions on the same bug, seed, solver revision, prompt version,
and available corpus:

1. **One-round**: one selection and one reasoning pass using up to 540 bytes of
   evidence.
2. **Two-round**: first retrieval and reasoning, a recorded missing-information
   query, second retrieval, then final reasoning. Across both reasoning calls,
   the sum of evidence bytes sent to the solver must not exceed 540. The second
   prompt may include prior evidence, but those repeated bytes count again.
3. **Repeat-reasoning control**: use the same first-round evidence in a second
   reasoning pass, with no new retrieval evidence. Apply the same 540-byte
   cumulative cap. This controls for an extra reasoning opportunity.
4. **All-evidence reference**: include all evidence and report its actual byte
   and token cost. This is a ceiling reference, not part of the equal-budget
   primary contrast.

Run conditions 1–3 for the lexical and EmbeddingGemma selectors and include
random selection as a control. Freeze selector and model revisions before
scored runs. If a model or method is unavailable, record it as unavailable
before scored runs; do not replace it after seeing outcomes.

## Budgets and cost records

The primary budget is 540 cumulative evidence bytes sent to the reasoning
model. For every run, record:

- unique evidence bytes retrieved;
- evidence bytes presented in each reasoning call and cumulative bytes;
- selector calls and query bytes;
- model input and output tokens by call;
- end-to-end latency and invalid outputs;
- duplicate evidence selected or re-sent.

Report the all-evidence condition separately. Do not equate bytes, tokens,
selector calls, or latency. The one-round and two-round success comparison is
matched on cumulative evidence bytes; iteration's extra selector and reasoning
cost remains visible in the cost report.

## Outcomes and estimands

### Primary outcome

**Final verified task success** is a binary result per run. Success requires a
correct root-cause statement and a repair that passes the locked regression
suite and defect-specific test, with no unrelated regression. A plausible
explanation or a passing test without the correct root cause is not sufficient.

**Primary estimand**: equal-weight mean across the predeclared independent bugs
of the within-bug success-rate difference (two-round minus one-round) at 540
cumulative evidence bytes. Average paired seeds within each bug first. Do not
weight bugs by their seed count or evidence count.

### Secondary outcomes

Report each separately by bug and condition:

- **First-round failure recovery**: fraction of runs that fail after round one
  but finish with verified success after round two; show the number eligible
  for recovery and the paired no-new-evidence result.
- **Evidence availability**: decisive-evidence recall by round and final
  evidence set.
- **Evidence sufficiency and interpretability**: blinded rubric outcomes from
  the frozen labels and solver explanation.
- **False-hypothesis confidence mass**: change from first to final reasoning on
  the same candidate set. Preserve the native score semantics; do not call it
  calibrated unless separately validated.
- **Contradiction handling**: unresolved labeled contradictions at each round.
- **Abstention**: correct abstention on insufficient-evidence tasks and
  unnecessary abstention on sufficient-evidence tasks.
- **False repair**: repair attempt that fails the defect test, gives a wrong
  root cause, or creates a locked regression.
- **Unnecessary re-retrieval**: second-round retrieval when first-round evidence
  was already independently judged sufficient and the second round adds no
  evidence that changes a locked outcome-relevant label.
- **Cost**: evidence bytes, tokens, selector calls, latency, and invalid output
  counts as listed above.

Do not collapse these outcomes into one score.

## Analysis plan

- Publish all per-bug paired outcomes and counts.
- Estimate the primary risk difference by averaging within each bug, then
  averaging bugs with equal weight.
- Form 95% uncertainty intervals by resampling bugs and keeping all seeds and
  conditions for a sampled bug together. Never bootstrap seeds as though they
  were independent bugs.
- Report raw per-bug differences because 20 clusters provide limited
  precision. A larger sample may be needed for a narrow interval.
- Analyze selector methods separately. Do not pool raw lexical scores and
  EmbeddingGemma cosine scores. Any mixture across selectors requires
  predeclared weights and a named estimand.
- Compare two-round retrieval with both the same-selector one-round condition
  and the repeat-reasoning control. Report all-evidence results separately.

## Decision and falsification rules

Before execution, the team must accept or amend these proposed decision margins:

- **Support a practical success benefit** if the primary risk-difference point
  estimate is at least +10 percentage points and its bug-level 95% interval is
  above zero. Also require the two-round minus repeat-reasoning-control
  difference to have a positive point estimate and a bug-level 95% interval
  above zero before claiming that new evidence adds value.
- **Require a false-repair safeguard**: the upper 95% interval for the
  two-round minus one-round false-repair difference must be below +5 percentage
  points before recommending the iteration path for further operational
  consideration.
- **Reject the practical-benefit claim for this tested setting** if the upper
  95% interval for the primary difference is below +10 percentage points.
- **Call the result harmful** if the primary interval is below zero or if
  false repairs increase beyond the predeclared safeguard.
- **Call the result unresolved** when the interval includes both no benefit and
  the +10-point minimum. Do not treat a non-significant result as evidence of
  equivalence.

The +10-point benefit and +5-point false-repair margins are proposed design
choices, not literature-derived constants. Freeze or replace them before any
scored run.

## Falsifiers and interpretation limits

The claim that a second retrieval adds value is weakened or falsified for this
setting if two-round retrieval does not improve verified success over the
same-selector one-round path, if the gain disappears against the
repeat-reasoning control, or if any gain requires a larger evidence budget.
More evidence recall without more success is not support for the primary
claim. More success with materially more false repairs does not pass the
safeguard.

Twenty bugs from a narrow source still support only a narrow claim. Validate
any result on distinct bugs and, before broad claims, on separate repositories
or task sources. This study alone cannot establish a Semadmit independence
rule. Such a handoff needs a reproducible held-out relation between a declared
shared factor and downstream error across independent bugs, and a comparison
with simpler rules for the named operation.

## Reproducibility record

Before execution, record the corpus and repository digests, bug and evidence
IDs, annotation and test versions, exact model tags and revisions, service
version, selector and prompt versions, random seeds, byte-count procedure,
invalid-output policy, all thresholds, and result file hashes. Preserve raw
retrieval traces and solver outputs. If any primary item changes after scored
runs begin, issue a dated amendment and keep the earlier run separate.
