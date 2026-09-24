# Feature 040 Convergence Record

**Date**: 2026-09-22
**Branch**: `codex/local-evidence-workbench`
**Base**: `main` at `3d0f22245a9d6ca666e4ffb54c3e415374784ade`

## Outcome

The implementation satisfies the feature requirements and plan; no remaining
code tasks were found. All 21 planned tasks are complete. The working branch is
still uncommitted and directly based on `main`.

The final review checked 15 functional requirements, 8 success criteria, 18
acceptance scenarios, the plan's architecture and constraints, and the five
constitution principles. No principle conflict or cross-family evidence
overclaim was found.

The independent reviewer found that AI4I's multi-mode-row count was absent from
its chart. The projection now includes “Rows with multiple modes,” the chart
labels state that counts overlap, and a test asserts the exact plotted value.
The reviewer also requested the full gate and convergence record; both are now
complete.

## Verification evidence

- `make check` passed: Ruff lint, repository format check, full pytest suite,
  branch-aware coverage generation and per-module 95% gate, dependency audit,
  and the synthetic demo.
- The generated coverage report records 96.48% branch coverage overall and
  98.00% combined coverage. Every production module passed the repository's
  per-module 95% branch-aware threshold.
- Focused workbench, repository, UI, and MetroPT-3 validation tests passed:
  `uv run pytest -o addopts= tests/test_workbench_datasets.py
  tests/test_workbench_repository.py tests/test_workbench_app.py
  tests/test_public_dataset_validation.py -q` — 86 passed.
- `uv lock --check` and `git diff --check` passed.
- `make workbench` started on `127.0.0.1:8501`; the Streamlit health endpoint
  returned `ok`. The same launch and health check succeeded with `UV_OFFLINE=1`.
  The smoke-test server was stopped afterward.
- An offline AppTest found all four examples and ran the explicit synthetic
  demo in 2.82 seconds, with no UI exceptions and an explicit synthetic label.
  This is automated UI timing, not a measured human walkthrough.
- The Repository Review button ran the real `make coverage` gate; AppTest
  observed both “passed in this session” and “artifact was refreshed” states.
- AppTest exercised all four verified chart pages, all four dataset path forms
  with warning and failure reports, missing AI4I input, repository gate
  pass/fail, and Graphify search without unhandled UI exceptions.
- The available Graphify JSON parsed as 3,541 nodes and 6,925 links; its
  recorded build commit differs from current `main`, so the UI correctly marks
  it potentially stale. Search and 60-node/200-link output bounds are tested.

## Limits and remaining manual checks

- No full public-dataset binaries were supplied or downloaded. Verifier behavior
  remains covered by the existing fixture-backed verifier tests; the new UI
  tests exercise the path/report seams with controlled verifier results. A
  reviewer can run each verifier against their own local dataset files.
- The installed `dot` executable was unavailable, so Graphviz source was not
  checked by the standalone Graphviz CLI and the chart was not visually
  inspected in a browser. Streamlit accepted the bounded chart component in
  AppTest, and its neighborhood-generation bounds are covered by tests.
- `pip-audit` reported no known vulnerabilities in packages it could audit;
  it skipped the local `isoprax-reference` distribution because it is not
  published on PyPI.

## Review follow-up — 2026-09-24

Review found that `urlsplit` treated Windows drive paths as URL schemes in the
workbench path validator. The shared URL check now preserves drive-prefixed
local paths, and a regression test covers `C:\\research data\\ai4i2020.csv`.

Current focused verification passed: the full suite reports 565 passed and 1
skipped with 98.00% total branch-aware coverage; every production module meets
the 95% branch-aware threshold. Ruff lint and formatting, `uv lock --check`,
the synthetic demo, and `git diff --check` passed. The notebook execution gate
also passes all five notebooks after the related Feature 041 review fixes.
All file-oriented pre-commit hooks passed; its contract-test hook was skipped
because the same full suite had just passed separately.
Hosted CI for PR #45 passed the Python 3.10, 3.12, and 3.14 test jobs and the
Ubuntu 3.10/3.12/3.14 plus Windows 3.12 notebook jobs.
