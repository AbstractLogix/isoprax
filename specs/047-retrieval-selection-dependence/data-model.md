# Benchmark Data Model: Retrieval and Interpretation Dependence

This is a proposed record shape for the next benchmark slice. It is not a runtime contract.

## Case

- **case_id**: stable case identifier.
- **stratum**: one of the declared evidence challenge types.
- **query**: selector and interpreter input.
- **initial_hypothesis**: optional fixed wrong hypothesis for a recovery case.
- **second_round_query**: optional query that includes the same frozen initial hypothesis for every selector in the repeated-selection probe.
- **gold_required_items**: item IDs needed for a complete answer, kept outside model inputs.
- **gold_answer**: locked task and root-cause labels.
- **permitted_operations**: operation IDs and their expected allow/refuse outcomes.
- **split**: development, rule-authoring, or held-out evaluation.
- **seed**: case-generation seed.

## Evidence item

- **item_id** and **case_id**.
- **source_record_id** and **upstream_source_ids**.
- **derivation_links** and duplicate-group identifier.
- **text** or content digest and stable source reference.
- **relevance_label**.
- **source_status**: verified, invalid, conflicting, or unknown.
- **operation_use_labels**.
- Gold labels remain outside selector and interpreter inputs.

## Selection event

- **case_id**, **condition_id**, and **budget_k**.
- **selector_pair_id** and combined-budget allocation when selectors are paired.
- **selection_round** and query digest.
- Exact model, selector, and revision identifiers.
- Shared base-model lineage where known.
- Corpus/index digest, tokenizer, prompt, software revision, decoding settings, and seed.
- Ordered selected item IDs, raw selector scores, and ranks.
- Deduplicated combined item IDs retain links to each selector event that returned them.
- Unknown lineage stays unknown.

## Interpretation event

- **case_id**, **condition_id**, and selected-item-set digest.
- Interpreter model and revision.
- Answer, root-cause ranking, confidence output if available, and abstention.
- Gold task and root-cause correctness.
- Retrieval-error and interpretation-error labels computed after the run.

## Score calibration

- Selector ID and score-calibration mapping revision.
- Development case/source split and held-out case/source split.
- Audited source-status target and explicit handling of unknown labels.
- Held-out Brier score, reliability-bin counts, calibration error, discrimination where defined, and prevalence baseline.

## Policy evaluation

- **case_id**, operation, policy ID, and expected permission.
- Policy permission, false permission, and unnecessary refusal.
- Ranking or declared downstream decision before and after policy.
- Held-out membership and policy-author identity.

A result must retain the case and selected-item links needed to recompute metrics. Aggregate metrics without those links are not sufficient for replay.
