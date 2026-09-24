# Tasks: Local Evidence Review Workbench

**Input**: Design documents from `specs/040-evidence-workbench/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/local-workbench.md`

**Tests**: Included because the specification requires report parity, fail-closed presentation states, local-only command behavior, and traceable chart values.

**Organization**: Tasks are grouped by user story. The shared command runner and optional app setup precede all stories.

## Phase 1: Setup

**Purpose**: Add the optional runtime and repository entry point without changing base-package dependencies.

- [x] T001 [P] Add the optional `workbench` dependency and resolve `uv.lock` in `pyproject.toml` and `uv.lock`.
- [x] T002 [P] Add the local `workbench` Make target and phony declaration in `Makefile`.
- [x] T003 [P] Create the repository-only app package initializer in `apps/evidence_workbench/__init__.py`.

## Phase 2: Foundational

**Purpose**: Establish the shared safe action seam used by the demo and explicit test/coverage review.

- [x] T004 Add fixed-action runner tests for the demo, coverage gate, timeout, missing executable, nonzero exit, and output truncation in `tests/test_workbench_repository.py`.
- [x] T005 Implement an allowlisted, bounded local action runner with no user-provided shell text in `apps/evidence_workbench/repository.py`.

## Phase 3: User Story 1 - Get oriented and try the synthetic demo (Priority: P1) 🎯 MVP

**Goal**: Explain all four evidence cases and make the existing synthetic demo runnable without dataset files.

**Independent Test**: With no dataset paths, view all four example cards, run the synthetic demo, and verify it is explicitly labeled synthetic and separate from public-data results.

### Tests for User Story 1

- [x] T006 [P] [US1] Test the four example descriptions, evidence classes, outcome labels, sources, and claim boundaries in `tests/test_workbench_datasets.py`.

### Implementation for User Story 1

- [x] T007 [US1] Add static, source-grounded example descriptions and safe reference links in `apps/evidence_workbench/datasets.py`.
- [x] T008 [US1] Implement the landing page and explicit synthetic-demo action/output in `apps/evidence_workbench/app.py`.

**Checkpoint**: A reviewer can understand the example set and run the synthetic demo without any public artifact.

## Phase 4: User Story 2 - Verify local dataset artifacts (Priority: P1)

**Goal**: Run each existing verifier from local paths and faithfully show reports and errors.

**Independent Test**: Use valid and malformed fixture artifacts for each verifier and confirm the workbench status/report matches the existing verifier without mutating inputs.

### Tests for User Story 2

- [x] T009 [P] [US2] Add shared MetroPT-3 manifest parser tests for valid, malformed, missing, and timezone-qualified input in `tests/test_public_dataset_validation.py`.
- [x] T010 [P] [US2] Test local-only path validation, per-dataset verifier dispatch, missing inputs, and report status in `tests/test_workbench_datasets.py`.

### Implementation for User Story 2

- [x] T011 [US2] Add the public MetroPT-3 interval-manifest parser in `isoprax/metropt3.py` and update `scripts/verify_public_dataset.py` to reuse it.
- [x] T012 [US2] Implement explicit local path handling, four verifier adapters, and not-run/verified/warnings/failed/unavailable result states in `apps/evidence_workbench/datasets.py`.
- [x] T013 [US2] Add dataset-specific local path forms, verify actions, status, provenance, diagnostics, and structured report inspection in `apps/evidence_workbench/app.py`.

**Checkpoint**: Each example can be independently verified; invalid or missing artifacts remain visible and do not crash the workbench.

## Phase 5: User Story 3 - Review evidence with dataset-specific graphs (Priority: P1)

**Goal**: Present fast, accurate visual summaries from verified reports without pooling outcomes.

**Independent Test**: Assert every chart row against verifier report fields for representative reports; verify modes remain overlapping, zero-yield projects remain visible, and MetroPT-3 uncovered observations remain censored.

### Tests for User Story 3

- [x] T014 [P] [US3] Test AI4I mode/discrepancy, ApacheJIT project/yield, C-MAPSS count/alignment, and MetroPT-3 coverage/cadence chart projections in `tests/test_workbench_datasets.py`.

### Implementation for User Story 3

- [x] T015 [US3] Implement pure per-dataset chart projections from successful native verifier reports in `apps/evidence_workbench/datasets.py`.
- [x] T016 [US3] Render titled/labeled dataset charts with visible text diagnostics and explicit censoring/outcome caveats in `apps/evidence_workbench/app.py`.

**Checkpoint**: All four verified examples have at least one report-derived graph; no aggregate or failed-input graph appears as verified evidence.

## Phase 6: User Story 4 - Review repository test and architecture signals (Priority: P2)

**Goal**: Explicitly run the bounded local coverage gate and inspect its result, coverage chart, and an optional bounded Graphify neighborhood.

**Independent Test**: Exercise controlled command success/failure, historical coverage, current coverage, missing/malformed/stale Graphify artifacts, and graph-size caps.

### Tests for User Story 4

- [x] T017 [P] [US4] Test branch-aware coverage parsing/freshness and Graphify schema/provenance/search/neighborhood bounds in `tests/test_workbench_repository.py`.

### Implementation for User Story 4

- [x] T018 [US4] Implement timestamped coverage-artifact reading and safe bounded Graphify JSON neighborhood generation in `apps/evidence_workbench/repository.py`.
- [x] T019 [US4] Add the repository review page with explicit coverage action/status, per-module chart, and optional searchable Graphify view in `apps/evidence_workbench/repository_view.py`.

**Checkpoint**: Current test status is distinct from prior artifacts; missing or stale graph data is unknown, never green.

## Phase 7: Polish and Cross-Cutting Validation

**Purpose**: Document the operator workflow, verify local safety and maintain all claims.

- [x] T020 [P] Document optional installation, loopback launch, data paths, charts, repository review, and evidence limits in `README.md` and `specs/040-evidence-workbench/quickstart.md`.
- [x] T021 Run the feature quickstart, focused/full tests, branch-aware coverage gate, lint/format checks, and local headless UI smoke test; record only observed results in `specs/040-evidence-workbench/converge.md`.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No code dependencies; optional dependency and entry point can be prepared independently.
- **Foundational (Phase 2)**: Depends on Phase 1; fixed action runner is shared by US1 and US4.
- **US1 (Phase 3)**: Depends on Setup and Foundational; first user-facing MVP.
- **US2 (Phase 4)**: Depends on Setup and Foundational; shares the app shell with US1 but not its demo results.
- **US3 (Phase 5)**: Depends on US2 because chart values require verifier reports.
- **US4 (Phase 6)**: Depends on Setup and Foundational; separate from dataset verification and visualization.
- **Polish (Phase 7)**: Depends on all four stories.

### User Story Dependencies

- **US1 (P1)**: Independent after the shared command runner; viable MVP without data files.
- **US2 (P1)**: Independent after the shared app and runner; reuses current verifier code and a public interval parser.
- **US3 (P1)**: Depends on US2 report adapters; charts are report projections, not separate validators.
- **US4 (P2)**: Independent of US2/US3 after the shared runner; uses local generated artifacts only.

### Parallel Opportunities

- T001, T002, and T003 touch separate files and can be prepared in parallel.
- Within US2, parser tests and path/adapter tests can be written in parallel; parser implementation and adapter/UI work should follow their respective tests.
- US1 and US4 can proceed independently after the shared runner, but their edits to `app.py` must be integrated sequentially.
- US3 chart projection tests precede the projection implementation; UI rendering follows both.

## Implementation Strategy

1. Establish the optional local entry point and safe fixed-action runner.
2. Deliver US1 as the no-data first-run MVP.
3. Add verifier-backed local inputs (US2), then report-derived graphs (US3).
4. Add maintainer coverage and Graphify review (US4) without merging those signals into dataset evidence.
5. Run convergence and the full repository gates; record evidence and remaining external/manual limits.

## Notes

- Every task is scoped to a named path and carries an ID; user-story tasks carry their story label.
- Tests cover fail-closed cases as well as successful cases. The optional app does not make the normal package or CI depend on Streamlit.
- Never interpret a chart, test gate, or Graphify structure as predictive efficacy or a cross-family conformance result.
