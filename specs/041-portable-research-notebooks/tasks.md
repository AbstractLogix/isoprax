# Tasks: Guided Research Notebooks

**Input**: Design documents from `specs/041-portable-research-notebooks/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, and `quickstart.md` are complete.

## Phase 1: Setup

- [X] T001 Add the optional locked `notebooks` dependency extra in `pyproject.toml` and resolve it in `uv.lock`.

## Phase 2: Foundational

- [X] T002 Add focused tests in `tests/test_notebook_support.py` for `required_dataset_path_fields()`, repository/data-root resolution, missing-input `not_run` behavior, verified report/chart projection, and chart suppression on failed reports.
- [X] T003 Expose the required dataset path fields in `apps/evidence_workbench/datasets.py` and implement shared local-path, verifier dispatch, report display, and verified-chart rendering helpers in `notebooks/__init__.py` and `notebooks/_support.py`.

## Phase 3: User Story 1 - Understand outcome boundaries

**Independent Test**: Execute `notebooks/00_outcome_commensurability.ipynb` offline; confirm it loads the four declared definitions, computes all pairwise results with `check_commensurable()`, and shows statuses without a pooled score.

- [X] T004 Create the outcome-definition notebook `notebooks/00_outcome_commensurability.ipynb`, including a report-derived direct/bridgeable/irreducible matrix and explicit pooling boundary.

## Phase 4: User Story 2 - Review a dataset with the authoritative verifier

**Independent Test**: Execute all four dataset notebooks with no data configured; confirm each reports expected local inputs as not run. Existing verifier/projection tests remain the positive and malformed-artifact integration evidence.

- [X] T005 Create `notebooks/01_ai4i2020.ipynb` using the AI4I verifier adapter and verified report projections; retain composite/mode overlap and synthetic-data boundaries.
- [X] T006 Create `notebooks/02_apachejit.ipynb` using the ApacheJIT verifier adapter and verified report projections; retain per-project volume and zero-yield labels.
- [X] T007 Create `notebooks/03_nasa_cmapss.ipynb` using the C-MAPSS verifier adapter per FD001-FD004 subset; retain train/test/RUL alignment and keep subsets separate.
- [X] T008 Create `notebooks/04_metropt3.ipynb` using the MetroPT-3 verifier adapter and pinned interval manifest; retain external-anchor coverage and censoring boundaries.

## Phase 5: User Story 3 - Run the same environment across supported setups

**Independent Test**: Install the locked optional environment and run `make notebook-check`; execute all five notebooks in CI on Ubuntu/Python 3.10, 3.12, and 3.14 plus Windows/Python 3.12, with no dataset files and no network access.

- [X] T009 Implement `scripts/check_notebooks.py` to validate v4 notebook schema and standard kernel metadata, reject saved outputs/execution counts and machine-specific paths, and execute notebook sources in memory with nbclient from the repository notebook directory.
- [X] T010 Add `notebooks/README.md` with launch, data-layout, path override, missing-input, kernel, and evidence-boundary guidance; document the notebook workflow in root `README.md`.
- [X] T011 Add isolated `notebooks` and `notebook-check` targets to `Makefile`, ignore local `data/` and Jupyter checkpoint files in `.gitignore`, and add the locked headless notebook job to `.github/workflows/ci.yml` on Linux Python 3.10/3.12/3.14 and Windows Python 3.12.

## Phase 6: User Story 2 - Add dataset-specific research investigations

**Goal**: Turn verifier-backed notebook shells into useful, evidence-aware analyses with tested split, metric, and alignment mechanics.

**Independent Test**: With no local dataset files, all notebooks still run offline and report `not_run`. Synthetic unit fixtures validate analytical helpers. With verified local files, each notebook shows its audit and dataset-specific analysis; only AI4I, ApacheJIT, and each C-MAPSS subset run fixed baselines. MetroPT-3 remains descriptive and censored.

- [X] T012 Add pandas to the optional `notebooks` extra in `pyproject.toml` and resolve the lock in `uv.lock`.
- [X] T013 [P] [US2] Add synthetic-fixture tests for ordered/temporal splits, feature leakage exclusions, unsupported classification metrics, C-MAPSS RUL/test-row alignment, and MetroPT-3 censoring in `tests/test_notebook_analysis.py`.
- [X] T014 Implement deterministic split, metric-support, RUL-alignment, and chunk-summary helpers in `notebooks/_analysis.py`, satisfying `tests/test_notebook_analysis.py` without adding APIs under `isoprax/`.
- [X] T015 [US2] Expand `notebooks/01_ai4i2020.ipynb` with label prevalence/overlap, feature distribution plots, and an ordered-UDI composite-failure baseline that excludes identifiers and mode labels.
- [X] T016 [US2] Expand `notebooks/02_apachejit.ipynb` with project/time yield audits and a commit-metric-only classifier using the disclosed 2017-01-01 UTC `author_date` holdout.
- [X] T017 [US2] Expand `notebooks/03_nasa_cmapss.ipynb` with separate unit/sensor trajectory exploration and per-subset RUL regression against official test targets and a training-median baseline.
- [X] T018 [US2] Expand `notebooks/04_metropt3.ipynb` with bounded chunked sensor summaries, measured cadence, and anchored interval views without constructing negatives or supervised scores.
- [X] T019 [US2] Update `notebooks/README.md` and the research-notebook section in `README.md` to explain analyses, splits, baselines, input requirements, and evidence limits.
- [X] T020 Validate the complete feature with `make notebook-check`, focused notebook-analysis/workbench tests, lock/lint checks, and the existing Python/platform CI matrix; record any unavailable external gate in `specs/041-portable-research-notebooks/converge.md`.

## Dependencies and Execution Order

- T001 precedes T009 and T011 because the optional notebook environment must be locked before launch/check targets are wired. T012 adds pandas to that same optional environment before analysis tests or data loading.
- T002 precedes T003. T003 precedes T004-T008.
- T013 precedes T014. T012 precedes running T013/T014. T014 precedes T015-T018.
- T015-T018 may proceed independently after T014. T019 follows their final notebook content. T020 follows all implementation and documentation tasks.
- T009 depends on T004-T008 existing; T010 and T011 can be finalized once the command and data convention are implemented.
- Recommended order: T001 → T002 → T003 → T004 → T005-T008 → T009-T011 → T012 → T013 → T014 → T015-T018 → T019 → T020.

## Validation

- `uv lock --check`
- `uv run --isolated --locked --no-default-groups --extra notebooks python scripts/check_notebooks.py`
- `uv run pytest tests/test_notebook_analysis.py tests/test_notebook_support.py tests/test_workbench_datasets.py -q`
- `uv lock --check`, `uv run ruff check .`, `uv run ruff format --check .`, and `git diff --check`
- Existing `make check` for repository-wide regression and coverage gates.

## Implementation Strategy

Preserve completed portability tasks. Add the optional pandas dependency, test notebook-analysis primitives before implementing them, then expand each dataset notebook independently behind its existing verification gate. Finish with user documentation and all focused and repository-wide gates. All notebook inputs remain optional and user-supplied; no benchmark binary is required in CI.

## Phase 7: Convergence

- [X] T021 Add a plot of the train-derived C-MAPSS RUL distribution per subset to satisfy the research plan's training life/RUL exploration decision (plan: C-MAPSS exploration; partial).
