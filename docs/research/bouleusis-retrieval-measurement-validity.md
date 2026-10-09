# Bouleusis Retrieval Results: Measurement Validity

**Status**: Reanalysis of the supplied Bouleusis JSONL; no new Bouleusis run was made.
**Source artifact**: `Bouleusis/docs/experiments/evidence-selection-sweep-2026-10-08.jsonl`
**Source SHA-256**: `0c186de744404ea39a33cc5625c2eaa52a4e6e9c398d489f9d32a237e446fb1c`

This assessment uses the trial records, not values copied from the summary table.
The JSONL is in the Bouleusis checkout. IsoPrax does not implement its
retrieval or deliberation behavior.

## 1. Reproduced findings from raw records

### Source and method

The source has 171 JSONL records: one metadata record and 170 run records. Its
metadata declares five arms, four byte-budget conditions, and seeds 32 through
41. The structure is complete for the declared design:

- Four selector arms × four budgets × ten seeds = 160 runs.
- One full-context arm × ten seeds = 10 runs. Those records use budget ID
  `unbounded`.
- There are no duplicate run IDs or duplicate arm/budget/seed keys. No expected
  run key is missing.

The metadata says the seeds vary hypothesis identifiers and order around the
same injected fault. The experiment therefore has one independent bug, not ten.

The reanalysis in [bouleusis-retrieval-sweep-reanalysis.json](bouleusis-retrieval-sweep-reanalysis.json)
retains all 170 run outcomes, seed IDs, selected evidence IDs, test and diagnosis
outcomes, abstention, event-derived false-belief claims, and costs. The
recomputation code is [reanalyze_bouleusis_sweep.py](../../scripts/reanalyze_bouleusis_sweep.py).

The analyzer independently recomputes decisive-evidence recall from the
selected and decisive evidence IDs. All 170 values match the stored recall.
It recomputes debugging success as a non-abstaining result with the correct
root-cause path and passing final tests. All 170 values match the stored
success field. It reconstructs final claim states from `claim_proposed`,
`belief_updated`, and `claim_retracted` events. For this artifact, false-belief
mass is the sum of nonzero confidence on a **concrete wrong-path claim** whose
final status is `supported`. All 170 event-derived claim lists and masses match
the stored `false_belief_persistence` fields.

The raw event records show the full-context false claim in every seed: the
solver retained `tests/test_app.py` as a supported cause with confidence
`1/6`, while the injected defect was in `src/config.py`. This mass is not a
calibration measure. An unlocalized “outside the listed candidates” claim is
not a concrete path claim and is not counted by this field.

### Matched-budget experiment: four bounded selectors at 540 bytes

Recall is the count of runs with decisive-evidence recall equal to 1.0.
Success and abstention are counts out of ten order trials. The repeated seeds
perturb one injected bug; they are not ten independent tasks.

| Bounded selector | Budget | Recall = 1 | Debug success | Abstain |
|---|---:|---:|---:|---:|
| Random | 540 bytes | 10/10 | 5/10 | 0/10 |
| Lexical | 540 bytes | 0/10 | 0/10 | 10/10 |
| EmbeddingGemma 2 | 540 bytes | 0/10 | 0/10 | 10/10 |
| Fixture-order positive control | 540 bytes | 10/10 | 10/10 | 0/10 |

For random, the successful order trials were seeds 32, 38, 39, 40, and 41;
seeds 33 through 37 failed. All ten selected the decisive evidence ID. This
reproduces 100% decisive-evidence recall and 50% debugging success exactly.
The per-run file preserves each selected evidence set and byte count.

**Decisive-evidence presence was not sufficient for successful debugging in
this fixture.**

### Other bounded budget conditions

These are separate conditions from the matched 540-byte comparison.

| Bounded selector | Budget | Recall = 1 | Debug success | Abstain |
|---|---:|---:|---:|---:|
| Lexical | 154 bytes | 0/10 | 0/10 | 10/10 |
| Random | 154 bytes | 8/10 | 0/10 | 2/10 |
| EmbeddingGemma 2 | 154 bytes | 0/10 | 0/10 | 10/10 |
| Fixture-order positive control | 154 bytes | 10/10 | 0/10 | 0/10 |
| Lexical | 455 bytes | 10/10 | 0/10 | 10/10 |
| Random | 455 bytes | 10/10 | 0/10 | 3/10 |
| EmbeddingGemma 2 | 455 bytes | 10/10 | 0/10 | 0/10 |
| Fixture-order positive control | 455 bytes | 10/10 | 0/10 | 0/10 |
| Lexical | 660 bytes, all evidence | 10/10 | 10/10 | 0/10 |
| Random | 660 bytes, all evidence | 10/10 | 10/10 | 0/10 |
| EmbeddingGemma 2 | 660 bytes, all evidence | 10/10 | 10/10 | 0/10 |
| Fixture-order positive control | 660 bytes, all evidence | 10/10 | 10/10 | 0/10 |

At the all-evidence bounded condition, all four selector arms converged to
the complete evidence set for each seed and each had 10/10 decisive-evidence
recall and 10/10 debugging success.

### Full-context reference

**Full-context reference: unbounded, 660 bytes.** It is a separate reference
condition, not a 540-byte selector arm. Its ten runs had 10/10 decisive-evidence
recall and 10/10 debugging success. Event-log reconstruction also found
non-zero false-belief persistence in every run: a concrete wrong-path claim
remained supported at confidence `1/6`. This is a within-condition result;
it does not establish that full context causes false beliefs or is
epistemically worse than bounded retrieval.

## 2. Supplied findings not independently reproducible

### Source-record discrepancy

The supplied summary labeled full context alongside the 540-byte condition.
The machine-readable records show that full context is logged separately as
unbounded and consumes 660 bytes. This reanalysis follows the raw records:
the matched 540-byte comparison contains only Random, Lexical, EmbeddingGemma
2, and the Fixture-order positive control. Full context is reported as a
separate reference condition. This is a summary-labeling discrepancy, not
corruption of the raw experiment records. No raw record was rewritten to match
the earlier summary.

The supplied 540-byte aggregate counts reproduce exactly for the four
bounded selectors. The all-evidence bounded-selector results and the separate
full-context reference outcomes also reproduce from their records. Their
condition labels must stay distinct.

The JSONL does not provide explicit labels for evidence relevance,
evidence sufficiency, interpretability, or unresolved contradiction. It
records an abstention flag, but not a gold sufficiency label that would make
abstention justifiable or unnecessary. It contains no iterative retrieval
round, so it cannot measure recovery from a second retrieval. It has one bug,
so it cannot estimate between-bug uncertainty, broad calibration, or
cross-problem generalization. It records final test status and runtime versions,
but not a source/test snapshot that would let this report rerun the debugging
tests. Thus success is reproducible as a recorded aggregate and internally
cross-checked against diagnosis and test-status fields; the test execution
itself is not independently replayed here.

## 3. Interpretation

### Recall, relevance, sufficiency, and success

The random arm is a direct counterexample to using decisive-evidence recall as
a sufficient proxy for success in this fixture: all ten 540-byte runs include
the decisive item, but five fail. Recall measures evidence availability. It
does not show that the solver recognized, understood, or used the item
correctly. The 455-byte condition adds another within-fixture counterexample:
all four selector arms have 10/10 recall and 0/10 success.

Keep these outcomes separate:

1. **Availability**: whether annotated decisive evidence was presented.
2. **Relevance**: whether an item bears on the query.
3. **Sufficiency**: whether the evidence can distinguish the correct resolution
   under a locked rubric.
4. **Interpretability**: whether the solver can explain what the evidence
   supports and what it does not support.
5. **Reasoning success**: whether the final diagnosis is correct and the repair
   passes the locked checks.
6. **Epistemic correctness**: whether support is assigned to the true hypothesis,
   false claims are reduced, contradictions are handled, and abstention matches
   evidence sufficiency.

The JSONL reproduces availability and task success. It does not contain all
labels needed for the other outcomes.

### Behavioral success and epistemic quality

The full-context reference solved the bug in all ten trials while the event
log retained `1/6` confidence on a supported false path in each run. Thus,
behavioral success and residual false-belief mass co-occurred in this
condition. This does not establish that full context caused the false belief
or that full context is epistemically worse than bounded retrieval. The
confidence mass is not calibrated probability.

Candidate outcomes answer different questions:

| Measure | Definition | Question answered |
|---|---|---|
| Verified task success | Correct diagnosis and passing locked checks | Did the investigation reach the behavioral endpoint? |
| True-hypothesis confidence | Final confidence on the annotated true cause | How much support did the solver give the correct explanation? |
| False-hypothesis mass | Final confidence on annotated false causes, with the native score semantics preserved | How much support remains on known-false explanations? |
| Unresolved contradictions | Labeled conflicts the solver neither resolves nor explicitly preserves as unresolved | Did it handle conflicting evidence? |
| Justified abstention | Abstention on independently labeled insufficient-evidence cases | Was abstention appropriate? |
| Belief recovery | First-to-final state change after new evidence, with final verified success | Did the new evidence correct an earlier state? |

Do not combine these measures into one “reasoning quality” scalar without a
validated construct and a declared use.

### Budget-dependent selector claims

The results vary by `selector × task × budget × downstream operation`. At 154
bytes, the positive control retrieved decisive evidence on all seeds but never
succeeded. At 455 bytes, all selector arms reached the decisive item but none
succeeded. At 540 bytes, random succeeded on five seeds and the positive control
on ten; lexical and embedding abstained on all ten. At 660 bytes, every
selector arm succeeded. These results support only a condition-specific
account. A selector has no single global quality value from this sweep.

### Score commensurability

Embedding cosine similarity, lexical overlap, decision probability, and
confidence are different score objects. The raw JSONL contains selection
traces, but this one bug and one decisive-evidence target do not establish a
shared numeric meaning, score calibration, threshold transfer, or valid pooling.
Do not pool the scores. If a future study tests a common outcome, fit each
mapping on development bugs and assess it on held-out bugs; retain the native
score meanings and report each target separately unless a weighted mixture
estimand was declared in advance.

### Current claim assessment

| Claim | Assessment from raw records |
|---|---|
| Decisive-evidence recall predicts task success | **Not supported as a sufficient proxy here.** At 540 bytes, aggregate success ranges from 0/10 to 10/10 across arms. In the random arm, all ten runs include decisive evidence but only five succeed. General prediction across bugs is unresolved. |
| Full-context success implies no residual false beliefs | **Not supported in this reference condition.** All ten runs succeeded and retained recorded false-belief mass. This does not establish a causal effect or a cross-condition epistemic ranking. |
| EmbeddingGemma is inferior to lexical retrieval | **Not established.** Both have floor outcomes at 540 bytes and both succeed with all evidence. This does not order their methods. |
| Learned retrieval is inferior to deterministic retrieval | **Not established.** Random recall is higher at some constrained budgets, but task success varies and there is one bug. |
| Iterative retrieval is necessary | **Not tested.** There is no iterative condition in the JSONL. |

### Metric and estimand map

| Measure | Unit and estimand | Valid comparison | Invalid shortcut |
|---|---|---|---|
| Availability | Decisive items present per bug-condition at each budget | Same decisive labels, task, and budget | Treat recall as success |
| Relevance | Relevant selected items among selected items | Same relevance annotations | Treat relevance as sufficiency or source validity |
| Sufficiency | Reviewer-rated sufficient cases per bug-condition | Same locked sufficiency rubric | Infer sufficiency from recall |
| Interpretability | Correct evidence explanation per bug-condition | Same solver, task, and blind rubric | Infer explanation quality from item count |
| Task success | Verified successes per independent bug | Paired arms on the same bug set | Treat order seeds as independent tasks |
| Epistemic state | True support, false-path mass, calibration where valid | Same hypothesis set and truth labels | Pool with task success |
| Contradictions | Unresolved labeled contradictions per bug-condition | Same contradiction set and rubric | Count any conflict as solver error |
| Abstention | Correct vs unnecessary abstentions by evidence sufficiency | Same sufficiency labels | Reward abstention without its evidence state |
| Belief recovery | Paired first-to-final change and verified outcome | New-evidence and no-new-evidence controls | Call any second retrieval recovery |

### Semadmit handoff

This dataset does not support an independence rule. Different selector IDs or
score forms do not prove independent errors. A future handoff requires a
reproducible, held-out relationship between a named shared factor and
downstream error across distinct bugs. Candidate factors are shared model,
encoder, corpus, and query construction. Compare joint error with component
error and with simpler rules for a named operation. Any proposal must state its
conditions, benefits, refusal cost, limits, and falsifier. There is no
Semadmit recommendation from the present sweep.

## 4. Prospective hypotheses

The current sweep contains no iterative retrieval. The prospective questions
are:

- Does a two-round retrieve/reason path improve final verified success over the
  same selector's one-round path at the same cumulative evidence-byte budget?
- Does new evidence improve the result beyond a second reasoning pass with no
  new evidence?
- What share of first-round failures recover after round two, and at what
  selector, evidence, token, and latency cost?
- Does iteration reduce false-hypothesis mass or unnecessary abstention without
  increasing false repair?

The [iterative-retrieval preregistration](iterative-retrieval-preregistration.md)
sets the proposed conditions, metrics, estimand, cost accounting, and decision
margins before any multi-bug iterative results. It remains a draft until exact
bug IDs, revisions, and run configuration are frozen. No outcome may be
inspected before that freeze.

## 5. Predeclared multi-bug analyses

### Independent problem counts

The independent unit is a distinct bug, not an order or hypothesis-ID variant.
This follows the general design principle that repeated observations from one
experimental unit do not create independent replicates. See
[Hurlbert (1984)](https://doi.org/10.2307/1942661). The counts below are
proposed design guidance, not sample-size thresholds from that paper.

| Distinct bugs | Supportable claim scope |
|---:|---|
| 1 bug × many seeds | Case study and repeatability under order variants for that bug only. |
| 10 bugs | Exploratory comparison across the selected cases; show per-bug results and heterogeneity. No broad task-population claim. |
| 20 bugs | Minimum initial panel for an estimate over a predeclared, sampled bug set. This may still be underpowered. |
| Larger corpus | Better support for broader estimates when bugs span root causes, repositories, and evidence shapes. Use a power or precision analysis and reserve independent bugs or repositories for validation. |

The proposed minimum is 20 distinct, independently reviewed bugs, with at
least five bugs in each of four predeclared root-cause or evidence-shape
strata. Pair conditions on each bug and use five paired seeds per condition.
Average seeds within bug, then give each bug equal weight. Resample bugs—not
seeds—for uncertainty, show all per-bug differences, and do not make subgroup
claims without adequate independent cases.

### Iterative-retrieval analysis

At 540 cumulative evidence bytes, compare:

1. one retrieval and one reasoning pass;
2. two retrieval rounds with an explicit missing-information query; and
3. two reasoning passes over the first-round evidence, with no new evidence.

Keep all-evidence performance as a separate ceiling reference and report its
actual cost. Record unique evidence bytes, bytes sent in each reasoning call,
selector calls, tokens, latency, duplicates, and invalid outputs. Measure final
success, first-round recovery, recall, sufficiency, interpretability, false
belief change, contradictions, abstention, false repair, unnecessary
re-retrieval, and cost as separate outcomes.

The prospective preregistration proposes a +10 percentage-point minimum useful
success gain and a +5-point upper bound for added false-repair risk. Support
requires the primary effect to meet the gain threshold with its bug-level 95%
interval above zero. To claim that new evidence adds value, the two-round minus
no-new-evidence-control difference must also be positive with its bug-level
95% interval above zero. An upper interval below the useful-gain threshold
rejects that practical claim for the tested setting. A wide interval spanning
both no effect and a useful gain is unresolved, not equivalence. Freeze or
amend these margins before any run.

The results remain limited to the sampled bugs, budgets, solver, and operation.
A Semadmit handoff requires an additional replicated held-out effect across
independent bugs and a comparison with simpler rules.
