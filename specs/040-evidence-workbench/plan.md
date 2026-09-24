# Implementation Plan: Local Evidence Review Workbench

**Branch**: `codex/local-evidence-workbench` | **Date**: 2026-09-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/040-evidence-workbench/spec.md`

## Summary

Add an optional local graphical workbench that makes the existing synthetic demo, four public-dataset verifiers, their distinct reports, and repository review artifacts easier to inspect. The app is an adapter over existing verifier logic. Dataset-specific charts are derived only from verified report values; repository test/coverage and Graphify review remain separate from evidence claims. Streamlit is selected as an optional extra, with its server bound to loopback and usage statistics disabled.

## Technical Context

**Language/Version**: Python 3.10–3.14, matching `pyproject.toml`.

**Primary Dependencies**: Existing Isoprax package and verifier modules; optional Streamlit >=1.64,<2. Native Streamlit charts cover bar, line, and Graphviz views; no plotting package is added directly.

**Storage**: User-selected local input files; existing ignored `coverage.json`; optional ignored `graphify-out/graph.json`. No database and no persisted UI state.

**Testing**: `uv run pytest tests -q` and `make coverage` (including per-module 95% branch-aware gate); focused tests for report-to-chart mappings, local command runner, coverage parsing, Graphify validation and bounded graph output; local headless HTTP smoke check for the optional app.

**Target Platform**: Local repository checkout in the project-supported Python/uv environment. The app listens on `127.0.0.1` only.

**Project Type**: Optional repository web UI alongside the existing Python library and CLI.

**Performance Goals**: Do not load full dataset contents into a second interactive table. Existing verifiers remain the only full-artifact scan. Graph view is bounded to a small neighborhood; local test action is time-limited and output-capped.

**Constraints**: Offline by default; no remote data access, file upload, arbitrary command execution, source mutation, or automatic Graphify generation. UI status distinguishes not-run, failed, verified-with-warnings, stale, and unavailable. Dataset outcomes remain unpooled.

**Scale/Scope**: Four dataset examples, one existing synthetic demo, one local test/coverage action, and an optional Graphify snapshot with the currently observed 3,541 nodes / 6,925 links.

## Constitution Check

| Principle | Gate | Design response |
|---|---|---|
| I. Specification Authority | PASS | UI text and result views preserve the repository's current specs and verifier reports; no new Isoprax conformance rule is introduced. |
| II. Honest Conformance | PASS | Synthetic, repository-derived, simulated, and externally anchored examples stay distinct. Structural reports are not efficacy or Semantic/Full Conformance. |
| III. Contract-First Testing | PASS | Pure report projections, status transitions, path parsing, output truncation, coverage ingestion, and Graphify bounds receive focused automated tests. |
| IV. Deterministic Core, Explicit Effects | PASS | Core verifier functions remain authoritative. Test/demo subprocesses are fixed allowlisted actions started only by explicit user interaction; there is no network adapter. |
| V. Minimal Reference Scope | PASS | Streamlit is optional and outside the installed core package. The workbench is a repository tool, not a new public product service. |
| Development Workflow | PASS | Spec Kit artifacts are maintained; dependency resolution and all execution use `uv`. |

## Design Decisions

1. **Keep the app optional and local.** Add a `workbench` optional dependency and a Make target. Bind Streamlit to `127.0.0.1` and disable usage statistics. Normal package installation and CI do not acquire Streamlit.
2. **Call existing verifier interfaces.** A thin dataset adapter receives explicit local paths and calls `verify_ai4i2020_csv`, `verify_apachejit_csv`, `verify_cmapss`, or `verify_metropt3_csv`. It does not duplicate validation or create a unified cross-family outcome model. Move MetroPT-3 interval-manifest parsing into a public, tested function in `isoprax.metropt3` so both CLI and UI use the same parser.
3. **Keep visual projections dataset-specific and pure.** Small functions map successful report fields to chart rows. Failed/unavailable reports show errors and no data plot. Chart headings identify the dataset, unit/metric, and evidence class; mode counts are explicitly overlapping where applicable, and MetroPT-3 uncovered rows remain censored.
4. **Make repository actions explicit and fixed.** Buttons may run only the existing synthetic demo and `make coverage`; use `subprocess.run` with argument arrays, repository cwd, captured bounded output, and a 10-minute test timeout. Do not expose a command field or run `make check` (which includes dependency audit).
5. **Separate current check status from stored coverage.** Only a command result from the current app session is labeled current pass/fail. Existing coverage JSON is independently labeled by its file timestamp. Branch-aware coverage is visualized only when the report metadata declares branch coverage.
6. **Treat Graphify as optional generated review data.** Read only `graphify-out/graph.json`, validate the expected nodes/links shape, compare its recorded commit with current HEAD, and warn if the worktree is dirty or provenance is absent. Render only a deterministic, capped node neighborhood through Streamlit's Graphviz chart; do not embed generated HTML or regenerate the graph.
7. **Keep local paths session-scoped.** Use text path fields rather than browser uploads; reject URL schemes and never write user paths or input data to reports.

## Project Structure

### Documentation

```text
specs/040-evidence-workbench/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/local-workbench.md
├── quickstart.md
└── tasks.md
```

### Source Code

```text
apps/evidence_workbench/
├── __init__.py
├── app.py                 # Streamlit page composition and explicit actions
├── datasets.py            # verifier dispatch and dataset-specific chart projections
├── repository.py          # fixed command runner, coverage report, Graphify view model
└── repository_view.py     # separate Streamlit presentation for repository signals

isoprax/metropt3.py        # shared public interval-manifest parser
scripts/verify_public_dataset.py  # reuse the shared interval parser
Makefile                   # optional local workbench target
pyproject.toml             # optional workbench dependency
uv.lock                    # resolved optional dependency
README.md                  # local install/run guide and scope boundaries

tests/
├── test_workbench_datasets.py
├── test_workbench_repository.py
└── test_public_dataset_validation.py  # shared interval parser regression cases
```

**Structure Decision**: Keep the UI in a repository-only `apps/` package, excluded from the published `isoprax` package. Pure adapters are separated from Streamlit rendering so normal CI can test them without installing the optional UI dependency. The repository-review presentation has its own module because it combines distinct coverage and Graphify states, while `repository.py` remains Streamlit-free. The sole `isoprax/` change is the reusable MetroPT-3 manifest parser, shared by two callers.

## Complexity Tracking

No constitution violations or additional service tiers are introduced. The optional UI and its adapter are justified by the requested human-review workflow; the base package remains unchanged at runtime.
