---
description: "Task list for IsoPrax research-scope refinement"
---

# Tasks: IsoPrax Research-Scope Refinement

**Input**: Design documents from `specs/045-research-scope-refinement/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md)

**Tests**: No test tasks. This feature changes public research documentation and does not change runtime behavior.

**Organization**: Tasks follow the three user stories in the specification.

## Phase 1: Setup

**Purpose**: Confirm the existing docs structure and the scoped feature artifacts are ready.

No repository initialization task is needed. `docs/research/` exists and this feature's spec, plan, research notes, and conceptual data model are in place.

## Phase 2: Foundational

**Purpose**: Establish common research terms and evidence boundaries before writing the story documents.

No software foundation is needed. The project constitution, v0.3 POC, and evidence boundary are named in the design artifacts.

## Phase 3: User Story 1 - Understand current scope and boundaries (Priority: P1)

**Goal**: Publish a traceable module audit and explicit public/private project boundaries.

**Independent Test**: A reviewer can locate a reasoned disposition for each major module group and explain the work owned by IsoPrax, Semadmit, and Bouleusis without finding any automatic code move.

- [x] T001 [US1] Write the module inventory, evidence-strength review, code dispositions, and next research question in `docs/research/project-scope-and-architecture.md`.
- [x] T002 [US1] Define the public research-to-enforcement handoff in `docs/research/isoprax-semadmit-boundary.md` and the research-to-deliberation handoff in `docs/research/isoprax-bouleusis-boundary.md`.

## Phase 4: User Story 2 - Evaluate commensurability research (Priority: P1)

**Goal**: Specify bounded research questions, operation conditions, a reproducible negative benchmark, and a shared-model experiment.

**Independent Test**: A reviewer can identify each operation's target and preconditions, reproduce the described synthetic setup from existing reference code, and state what result would falsify each proposed claim.

- [x] T003 [US2] Write the evidence taxonomy, literature boundary, hypotheses, and open questions in `docs/research/evidence-commensurability.md`.
- [x] T004 [US2] Define operation-level preconditions and allowed, conditional, disallowed, or unknown results in `docs/research/operation-specific-commensurability.md`.
- [x] T005 [US2] Specify the invalid-aggregation benchmark, valid control, expected outputs, measures, and claim boundary in `docs/research/invalid-aggregation-benchmark.md`.
- [x] T006 [US2] Specify the shared-model, multiple-outcome experiment, controls, splits, measures, and falsifier in `docs/research/shared-model-commensurability-experiment.md`.
- [x] T007 [US2] Consolidate measurable negative results and stop conditions in `docs/research/falsification.md`.

## Phase 5: User Story 3 - Discover the public research program (Priority: P2)

**Goal**: Make the mission and research path easy to find while preserving the implementation history.

**Independent Test**: A new reader sees the mission and thesis before Stage 0/1/2 details and can navigate from the README to every research document.

- [x] T008 [US3] Create the linked research index and classify repository evidence, literature, hypotheses, and planned experiments in `docs/research/README.md`.
- [x] T009 [US3] Put the research mission and thesis before the implementation stages and link the research index in `README.md`.

## Phase 6: Polish and Cross-Cutting Review

**Purpose**: Check that the report matches the repository and that the new public documents agree.

- [x] T010 Review every repository path, internal link, claim label, and code disposition in `docs/research/` and `README.md`; run `git diff --check` without modifying Feature 044 files.

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No action is required; the repository and document area already exist.
- **Foundational (Phase 2)**: No action is required; the constitution and current evidence boundary are documented in the feature plan.
- **User Story 1 (Phase 3)**: Can proceed from the current repository inventory.
- **User Story 2 (Phase 4)**: Uses the existing OutcomeDefinition and pooling-harm evidence described in the plan; it does not depend on code movement.
- **User Story 3 (Phase 5)**: Depends on the research documents being present so that all links resolve.
- **Polish (Phase 6)**: Depends on all documents being present.

### User Story Dependencies

- **US1 (P1)**: Independent; produces the audit and two responsibility-boundary documents.
- **US2 (P1)**: Independent as a research document set; preserves the distinction between current evidence and new hypotheses.
- **US3 (P2)**: Depends on the destination files from US1 and US2 for complete navigation.

## Implementation Strategy

Complete the audit and research documents first. Update the README and research map after the destination pages exist. Finish with a path, claim-boundary, and whitespace review. Do not change application code or run tests for this documentation-only feature.
