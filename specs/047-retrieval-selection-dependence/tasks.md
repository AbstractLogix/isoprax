---
description: "Research note and benchmark protocol tasks"
---

# Tasks: Retrieval and Interpretation Dependence

**Input**: Design documents in this directory and the user's research request.

**Organization**: The research-design slice is complete. The implementation and execution slice is now active.

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

- [ ] T012 Execute all primary conditions, evidence budgets, repeated-selection probes, and selector-pair probes with the pinned local model digests.
- [ ] T013 Repeat the run and verify the case, selection, and result digests; save canonical results to **docs/research/retrieval-selection-dependence-results.json**.
- [ ] T014 Write **docs/research/retrieval-selection-dependence-results.md** with per-condition results, uncertainty, H1-H5 assessment, evidence classes, limits, and next tests.
- [ ] T015 Update the research index, quickstart, and convergence record; assess whether any bounded Semadmit review is warranted.
