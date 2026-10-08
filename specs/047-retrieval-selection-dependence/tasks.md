---
description: "Research note and benchmark protocol tasks"
---

# Tasks: Retrieval and Interpretation Dependence

**Input**: Design documents in this directory and the user's research request.

**Organization**: The research-design slice is complete. The implementation, model-compatibility, and execution slices are now active.

## Phase 1: Establish evidence boundaries

**Goal**: State what the primary paper and existing repository results do and do not establish.

- [x] T001 Write **docs/research/retrieval-selection-dependence.md** with paper claims, limits, prior repository evidence, hypotheses, ownership boundaries, and evidence-based recommendation.
- [x] T002 Record the primary source and the research gap in **specs/047-retrieval-selection-dependence/research.md**.

## Phase 2: Specify the controlled study

**Goal**: Make the future benchmark executable without inventing its question or measures.

- [x] T003 Write **docs/research/retrieval-selection-dependence-benchmark.md** with conditions A-D, evidence types, provenance, budgets, realized-budget-matched selector-pair corroboration, held-out score calibration, simple-rule baselines, analysis, falsification, and handoff criteria.
- [x] T004 Define the proposed case, evidence, selection, interpretation, and policy records in **specs/047-retrieval-selection-dependence/data-model.md**.
- [x] T005 Write the scope, plan, checklist, and quickstart for this documentation slice and its next implementation slice.

## Phase 3: Link and review the research artifacts

**Goal**: Make the new thread easy to find and verify its scope.

- [x] T006 Add the research note and benchmark protocol to **docs/research/README.md**; review source links, local links, required measures, and scope boundaries.
- [x] T007 Record the completed requirements and remaining benchmark-execution boundary in **specs/047-retrieval-selection-dependence/converge.md**.

## Phase 4: Freeze and implement the pilot

**Goal**: Make the synthetic run reproducible and keep labels out of selector and interpreter inputs.

- [X] T008 Freeze model digests, seeds, case count, strata, splits, metrics, and decision thresholds in **preregistration.json** before model execution.
- [X] T009 Implement the case generator, BM25 and prompted selectors, local model client, and exact selection trace in **scripts/retrieval_dependence_experiment.py**.
- [X] T010 Implement held-out interpretation, paired error metrics, score calibration, selector-pair controls, and the four policy baselines.
- [X] T011 Add focused tests for deterministic generation, prompt-label separation, parsing, budgets, metrics, policy outcomes, and canonical serialization.

## Phase 5: Execute and report

**Goal**: Run the frozen synthetic study, check replay, and state the evidence limits.

- [x] T012 Execute all primary conditions, evidence budgets, repeated-selection probes, and selector-pair probes with the pinned local model digests.
- [x] T013 Repeat the run and compare case, selection, and result digests; preserve both raw runs and report the complete-result mismatch in **docs/research/retrieval-selection-dependence-results.json.gz**.
- [x] T014 Write **docs/research/retrieval-selection-dependence-results.md** with per-condition results, uncertainty, H1-H5 assessment, evidence classes, limits, and next tests.
- [x] T015 Update the research index, quickstart, and convergence record; assess whether any bounded Semadmit review is warranted.

## Phase 6: Implement the model-role experiment

**Goal**: Compare each requested model role on named synthetic targets without treating its output scale or model identity as semantic evidence.

- [ ] T016 Freeze exact available model tags, selected manifest digests, Ollama version, fixture hashes, prompts, split, weights, and bootstrap seeds in **model-role-preregistration.json**. Do not begin scored calls while any requested role has an unresolved identity.
- [ ] T017 Implement deterministic Tev1 binary, categorical, and ordinal fixture generation with native `/v1/systemone` output parsing and per-family metrics.
- [ ] T018 Implement the shared evidence-relevance fixtures, EmbeddingGemma, Tev1, Qwen, Gemma, Coder, and Guardian adapters. Preserve each role's native output form and record invalid output without imputing it.
- [ ] T019 Implement development-only calibration, per-domain held-out metrics, ranking and threshold-change analysis, Qwen/Gemma/Guardian error dependence, predeclared pools, and Coder-by-family comparisons.
- [ ] T020 Add focused deterministic tests for fixture stability, split and label isolation, output parsers, calibration, bootstrap units, pooling, and result digests.

## Phase 7: Execute model-role comparisons and report

**Goal**: Run the frozen synthetic model-role suite twice and publish bounded findings.

- [ ] T021 Execute and replay the complete model-role suite; retain both raw result files and compare fixture and configuration digests.
- [ ] T022 Write **docs/research/model-role-commensurability-results.json** and **docs/research/model-role-commensurability-results.md** with per-target calibration, discrimination, sample counts, event rates, uncertainty, dependence, pooling, ranking, and role-by-family results.
- [ ] T023 Update the quickstart, research index, and convergence record. State which IsoPrax rules may be proposed for Semadmit review, which hypotheses were weakened or falsified, and the next experiment.

## Phase 8: Assess Bouleusis retrieval outcomes

**Goal**: Assess the supplied retrieval sweep as a measurement-validity problem and define the next multi-bug study without implementing Bouleusis behavior.

- [x] T024 Write **docs/research/bouleusis-retrieval-measurement-validity.md**. Recompute the Bouleusis JSONL aggregates, preserve per-run outcomes and source hash, separate non-reproducible summary claims, assess recall versus downstream success and epistemic outcomes, and state the pseudo-replication limit.
- [x] T025 Write **docs/research/iterative-retrieval-preregistration.md** with a prospective multi-bug design, equal-budget and repeated-reasoning controls, metric/estimand definitions, cost accounting, and falsification criteria.
- [x] T026 Link the report and protocol from the research map and current retrieval-dependence note; preserve Bouleusis and Semadmit ownership boundaries.
