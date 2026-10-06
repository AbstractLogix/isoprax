---
description: "Implementation tasks for the IsoPrax commensurability experiments"
---

# Tasks: Commensurability Experiments and Evidence

**Input**: Design documents in `specs/046-commensurability-experiments/`.

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/experiment-result.md`, `quickstart.md`.

**Tests**: Focused runner tests are required by the user request and project constitution.

**Organization**: Tasks follow the four user stories. The synthetic runner and evidence report are the deliverable.

## Phase 1: User Story 1 - Audit baseline and public responsibilities (Priority: P1)

**Goal**: Correct the historical baseline statement and remove private/business-state assumptions from public boundaries.

**Independent Test**: Check commit ancestry/tree statements and search the three boundary documents for private/proprietary assumptions.

- [x] T001 [US1] Update `docs/research/project-scope-and-architecture.md` to assess tracked Feature 044 ancestry, list excluded uncommitted qualification paths, and classify the bounded Haskell oracle.
- [x] T002 [US1] Rewrite `docs/research/isoprax-semadmit-boundary.md` and `docs/research/isoprax-bouleusis-boundary.md` with implementation-neutral ownership terms.

## Phase 2: User Story 2 - Reproduce Benchmark A (Priority: P1)

**Goal**: Produce deterministic different-target and same-target control outputs.

**Independent Test**: Benchmark lane metrics match the declared 100-row setup; repeated runner outputs are byte-identical.

- [x] T003 [US2] Implement the deterministic Benchmark A fixtures and exact mixture estimand in `isoprax/research_experiments.py`.
- [x] T004 [P] [US2] Add focused Benchmark A and no-implicit-pooling tests in `tests/test_research_experiments.py`.
- [x] T005 [US2] Add stable JSON serialization and the `python -m isoprax.research_experiments` entry point.

## Phase 3: User Story 3 - Run shared-model and gate comparisons (Priority: P1)

**Goal**: Exercise one JEPA backend across family and horizon differences, and compare four permission rules.

**Independent Test**: The output shows one shared backend ID, target-local metrics for three controls, declared same-target pooling only, and full error/rank/decision metrics for all four rules.

- [x] T006 [US3] Add deterministic synthetic JEPA training, calibration, and test splits for family, horizon, and same-target cases in `isoprax/research_experiments.py`.
- [x] T007 [P] [US3] Add per-target metric, bootstrap uncertainty, rank, and mixture guard assertions in `tests/test_research_experiments.py`.
- [x] T008 [US3] Implement the fixed gate challenge matrix and naive, global-label, metadata-only, and operation-specific rule summaries in `isoprax/research_experiments.py`.
- [x] T009 [US3] Measure false permissions, unnecessary refusals, interpretation errors, rank changes, and selected-record changes under the declared top-20% decision rule.

## Phase 4: User Story 4 - Publish evidence and boundaries (Priority: P2)

**Goal**: Publish a complete evidence report and exact generated results with clear evidence classes.

**Independent Test**: A reader can answer all five user questions and reproduce the result from the linked command.

- [x] T010 [US4] Execute the runner and save canonical output to `docs/research/experimental-results.json`.
- [x] T011 [US4] Write `docs/research/experimental-evidence.md` with results, limits, five answers, and repository/literature/experiment/hypothesis sections.
- [x] T012 [US4] Update Benchmark A, shared-model protocol, operation gate proposal, falsification criteria, and research map to link to executed results.

## Phase 5: Polish and Convergence

**Purpose**: Check deterministic behavior, claim boundaries, code quality, links, and remaining scope.

- [x] T013 Run the focused research, JEPA, and Haskell semantic-oracle tests; run Ruff on changed Python files; run the runner twice and compare canonical JSON.
- [x] T014 Check `git diff --check`, all new local paths and links, the bounded Haskell scope, and the Feature 044 worktree preservation; record results in `converge.md`.

## Dependencies

`T001-T002` can proceed independently of experiment code. `T003-T005` establish the runner. `T006-T009` depend on the runner's deterministic data/metric helpers. `T010-T012` depend on all experiment sections. `T013-T014` are final gates.

## Implementation Strategy

Implement the minimum deterministic fixtures and their contract tests first. Add target-local JEPA results and the rule comparison next. Generate the committed result only after all focused tests pass. Finish with the evidence report and a convergence check. No task changes runtime admission, deliberation, or the Haskell oracle.
