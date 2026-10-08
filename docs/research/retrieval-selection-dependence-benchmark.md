# Retrieval and Interpretation Dependence: Benchmark Specification

**Status**: Pre-execution protocol. No benchmark result is available.
**Evidence class**: The initial benchmark must be synthetic and explicitly labeled synthetic.
**Scope**: Test selection provenance and downstream interpretation. Do not implement a retrieval library or reproduce UNREAL.

## Question and hypotheses

Test whether shared selector/interpreter lineage changes selection and interpretation errors, whether those errors affect a named downstream operation, and whether simple metadata rules explain the result.

Use H1-H5 from [the research note](retrieval-selection-dependence.md). Record the hypotheses and analysis choices before running any condition. Do not use this protocol as evidence that a proposed effect exists.

## Conditions

Keep the candidate corpus, query, evidence labels, evidence budget, interpreter prompt, decoding settings, and evaluation cases fixed within paired comparisons.

| ID | Selector | Interpreter | Main comparison |
|---|---|---|---|
| A | BM25 lexical selector | Model X | Independent lexical baseline |
| B | External learned Retriever Y | Model X | Learned external selector vs A |
| C | Model X representation-based selector proxy | Model X | Same-model selection and interpretation vs A and B |
| D | The same Model X selector as C | Model Y | Interpreter-lineage control vs C |

The initial study may use a bounded model-native proxy for C. Record its design and revision. Label it as a proxy. Do not claim that proxy results establish a property of UNREAL.

Pin Model X and Model Y by full model and revision identifiers, not display names. Record selector revision, index and corpus digest, tokenizer, prompt, decoding parameters, software version, and run seed. Record shared base-model lineage separately from exact model identity. If a required model or immutable revision cannot be identified, do not report that condition as a completed comparison.

An oracle-evidence control may give an interpreter only the gold decisive items. Use it to estimate interpretation performance when retrieval succeeds. Do not include it as one of the four primary selector conditions.

## Cross-selector corroboration probe

Test whether outputs from different selectors provide independent corroboration. For selector pairs A+B, A+C, and B+C, combine the unique selected items under one fixed Model X interpreter. At combined budgets 2, 4, 8, and 16, give each selector half of the budget. Compare each combined set with each selector's own top-k set at the same total budget. The one-item budget does not apply to this pair probe.

Keep selector identity and source lineage separate. If both selectors return the same item, deduplicate it in the combined context and do not count it as two sources. Measure item overlap, shared upstream source coverage, paired false-positive selection, and false corroboration: two or more selected items support the same incorrect root cause or are presented as independent when their gold source lineage overlaps or their source status is not verified. Keep the gold source and claim labels outside model inputs.

Report whether using two selectors reduces or increases false corroboration and interpretation errors against the equal-budget single-selector controls. Different selector IDs alone do not make evidence independent.

## Synthetic case set

Each case has 16 candidate evidence items. Include cases with:

- decisive relevant evidence;
- irrelevant evidence;
- plausible but non-decisive distractions;
- misleading evidence that appears relevant;
- duplicate items;
- items derived from one upstream record;
- conflicting evidence;
- a known initial wrong hypothesis in selected cases, so the study can measure whether later selection repeatedly supports it.

A case record must hold its gold labels outside the selector and interpreter inputs. Review the labels independently before running the conditions. Keep a held-out set whose labels and cases are not used to tune selectors, prompts, or operation rules.

For a dedicated repeated-selection probe, give each selector the same frozen, known-wrong initial hypothesis as part of a second-round query. Keep the candidate pool fixed. Measure the share of newly selected items that support or contradict that hypothesis. This is a benchmark probe, not an IsoPrax reasoning or orchestration feature.

For each item, store its item ID, case ID, source record ID, upstream source IDs, derivation links, selector and model lineage, rank, score, evidence budget, relevance label, source-status label, and operation-specific use labels. Preserve the exact item text or a content digest and a stable reference to it. Record missing or uncertain provenance as unknown; do not infer independence from absent metadata.

Keep three judgments distinct:

- relevance to the query;
- source status: verified, invalid, conflicting, or unknown;
- permission to use the item for the named operation.

The selector score is not a source-status label and is not confidence in evidence validity.

## Evidence budgets

Run each primary condition with top-k budgets of 1, 2, 4, 8, and 16 items. The 16-item case pool makes every budget available. Keep all other case content fixed across budgets.

Test whether interpretation improves, stays flat, or declines as k grows. Analyze each case stratum as well as the overall result. Do not assume that a larger budget harms performance or that a single budget is optimal.

## Measures

### Retrieval

For each condition and budget, report:

- recall@k and precision@k for relevant items;
- complete-evidence recall@k when a task needs a set of decisive items;
- rank of each decisive item;
- selection of misleading, duplicate, conflicting, and shared-upstream items.

State the denominator for each metric. Do not treat duplicate copies or descendants of one record as independent source coverage.

### Interpretation

Report per case and by stratum:

- task accuracy and root-cause accuracy;
- false-belief rate;
- recovery rate after a misleading item is present;
- abstention rate and abstention quality;
- root-cause ranking and the change in rank of the correct cause.

Define accuracy labels and acceptable abstention before the run. Do not use selector scores as interpreter confidence unless a separate, held-out calibration procedure is declared.

### Error dependence

Define retrieval error before execution. At minimum, count a retrieval error when a required decisive item is absent from the selected set or a pre-labeled misleading item outranks it within the budget. Define interpretation error from the locked answer key.

Report:

- overall retrieval-error and interpretation-error rates;
- P(interpretation error | retrieval error);
- P(interpretation error | no retrieval error);
- the paired risk difference between those probabilities;
- binary error correlation with a confidence interval;
- correlated false positives by case stratum;
- the rate that later selected items support a pre-labeled wrong initial hypothesis.

Use paired case-level analysis across A-D. Report uncertainty intervals and sample counts. Keep case generation, model variation, and bootstrap uncertainty separate. A confidence interval over cases does not measure uncertainty over all models or real-world domains.

Compare A with C while Model X interprets both. Compare C with D while the selector and selected item set stay fixed. Compare B with A for the effect of replacing the lexical selector with the external retriever. Report retrieval quality and interpretation quality together; do not attribute an interpretation difference to lineage if the selected sets differ without a matched-context replay.

### Retrieval score and source status

On held-out cases, test whether selector score ranks verified items above invalid or unknown items. Report the measure and its uncertainty separately from relevance retrieval metrics. Do not call the score a probability or confidence unless it is separately calibrated and validated for that target.

For H2, compare paired changes in retrieval measures with paired changes in interpretation accuracy and source-status selection. Report cases where retrieval improves but interpretation does not improve. If the outcomes move together in this benchmark, state that this run did not show a mismatch; do not infer that retrieval recall guarantees epistemic reliability in other settings.

For H4, compare held-out error prediction using source and derivation metadata alone with the same simple analysis after adding selector/interpreter lineage fields. Report the paired change in held-out log loss with uncertainty. Do not use this diagnostic as a causal claim.

### Retrieval score as evidence confidence

Test score calibration against independently adjudicated source status, not relevance. For each selector, fit one predeclared calibration mapping on development cases from raw score to the probability that an item is source-verified. Evaluate it only on held-out cases. For the primary binary calibration target, use verified versus audited invalid/conflicting items. Exclude unknown-status items from that fit and report them separately; do not silently treat unknown as invalid. Report held-out Brier score, reliability bins, calibration error, discrimination where the labels support it, and the training-prevalence baseline. Split by case and source lineage to prevent items from one source appearing in both calibration and held-out sets.

A calibrated score for source verification in this fixture still does not prove operation admissibility or independence. If calibration does not improve held-out results over the base-rate prediction, retain the score as a ranking signal only.

### Simple-rule comparison

Evaluate the same locked cases using four policies:

1. **Naive aggregation**: treat each selected item as independent support and use the selector score as confidence. This is an intentionally unsupported baseline, not a proposed IsoPrax rule.
2. **One global label**: set one case-level dependence label from the shared selector/interpreter lineage field, then apply it to every operation. This ignores item-level provenance and operation requirements.
3. **Metadata-only rule**: deny an independence claim for duplicates, shared upstream source records, or declared shared selector/interpreter lineage; otherwise allow it. This rule does not inspect operation-specific validity conditions.
4. **Operation-specific rule**: check source status, provenance, selector/interpreter lineage, and the named operation's declared requirements.

Before execution, define the reference answer for whether each operation is allowed. Hold out cases from rule authors. Report false permissions, unnecessary refusals, interpretation errors, ranking changes against the naive baseline, and decisions changed by each rule. If a downstream decision is measured, name the decision rule and threshold before execution. Do not report a decision-change count without a declared decision.

This comparison can show that a simpler rule performs as well as the operation-specific rule. That is a valid result and weakens the case for added complexity.

## Analysis and decision gates

Freeze the model revisions, case count, seeds, case strata, metric definitions, held-out split, uncertainty method, and any minimum practically meaningful effect before the run. Store this preregistration with the result. Do not choose a favorable budget, stratum, or threshold after inspecting results. Use 95% paired bootstrap intervals over case IDs, stratified by case type; resample repeated model runs separately when present.

Use paired comparisons on the same cases. Report effect estimates and uncertainty, not only significance labels. Repeat the synthetic run from the recorded seed and verify that the case and result digests match. If any model service is nondeterministic, record repeated runs and treat run variation separately from case sampling.

The study supports H1 only if the predeclared same-model contrast shows a repeatable increase in the retrieval/interpretation error association in at least one named misleading-evidence condition, with uncertainty and a downstream effect reported. The contrast must compare C with A on the same cases, and must exceed the predeclared minimum effect. A difference in retrieval recall alone does not support H1.

The study weakens or rejects the proposed need for added complexity if any of these results holds:

- C does not increase selection/interpretation error dependence over A in the predeclared misleading-evidence cases.
- Selector/interpreter lineage adds no predictive value after source and derivation metadata.
- The one global shared-lineage label predicts the useful outcomes as well as the operation-specific rule.
- Error dependence changes but does not change interpretation quality or any predeclared operation decision.
- No tested case stratum shows a reproducible decline as k grows.
- The operation-specific rule does not improve held-out results over the simpler metadata-only rule.

Report null and adverse results. Do not infer operational value from a statistical dependence result without a measured downstream effect.

Do not send a Semadmit handoff from a synthetic result alone. A later handoff requires a reproducible effect on held-out cases, a declared operational condition, scope and limitations, a falsifier, and the metadata needed to identify the condition. Semadmit decides whether to operationalize it.

## Next implementation slice

The next slice should implement and execute this protocol as a deterministic synthetic benchmark. It should:

1. freeze the case generator, labels, splits, seeds, and analysis choices before results;
2. implement conditions A-D and record all model and source lineage;
3. run every budget and preserve exact selected-item lists;
4. compute the retrieval, interpretation, and dependence measures above;
5. compare all four rules on held-out cases;
6. save machine-readable results and a report that labels the study synthetic;
7. evaluate each hypothesis and state whether a Semadmit review is warranted.

This slice must not add an IsoPrax retrieval product, choose evidence for Bouleusis, reproduce UNREAL, or add runtime admission or enforcement.
