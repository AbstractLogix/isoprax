# Implementation Plan: Guided Research Notebooks

**Branch**: `codex/local-evidence-workbench` | **Date**: 2026-09-23 | **Spec**: [spec.md](spec.md)

## Summary

Keep the portable five-notebook set and extend the four dataset examples beyond verifier summaries. Each notebook first uses the existing evidence-workbench verifier; only verified local artifacts enter read-only data exploration. A small notebook analysis module will provide tested split/metric/alignment helpers. AI4I 2020 and ApacheJIT get fixed binary-classification baselines, each with a disclosed ordered/temporal holdout. C-MAPSS gets one fixed RUL regression baseline per official subset using train-derived RUL and the official test RUL vector. MetroPT-3 gets chunked sensor timelines and anchored-window views, but no supervised score because the stream is otherwise unlabeled/censored. No dataset acquisition, new core APIs, or cross-family efficacy claim is added.

## Technical Context

**Language/Version**: Python `>=3.10,<3.15`

**Primary Dependencies**: Existing Isoprax verifiers and workbench projections; optional notebook extra with JupyterLab, IPython kernel, nbformat, nbclient, Matplotlib, and pandas. NumPy and scikit-learn are already core dependencies.

**Storage**: Read-only user-supplied dataset files. No data copy, network access, or saved notebook outputs. MetroPT-3 analysis streams bounded CSV chunks and retains only hourly means plus minute means inside bounded anchor-context windows.

**Testing**: Unit tests exercise notebook-analysis split, leakage-exclusion, metric-support, RUL alignment, and censoring helpers on explicitly synthetic fixtures. `scripts/check_notebooks.py` continues to execute every no-data notebook path and enforce clean portable notebook files. Existing verifier and workbench tests remain authoritative for artifact validation.

**Target Platform**: Repository-supported Python versions on Ubuntu (3.10, 3.12, 3.14) and Windows (3.12) through the locked `uv` notebook extra.

**Project Type**: Repository-only research material; notebook analysis is not part of the published Isoprax package.

**Performance Goals**: No-data CI remains bounded by notebook startup and headless execution. ApacheJIT and C-MAPSS baselines use fixed low-complexity models. MetroPT-3 analysis has bounded memory independent of full CSV size through chunked reading.

**Constraints**: Verification gates precede analysis. Splits and feature exclusions are explicit and deterministic; held-out data are not tuned against. Class metrics without support are marked not estimable. MetroPT-3 observations outside external intervals remain censored. Public benchmark results remain per-dataset, per-subset, and exploratory. Synthetic AI4I results do not establish predictive efficacy. No scores are pooled across families.

## Constitution Check

| Principle | Gate | Design response |
|---|---|---|
| I. Specification Authority | PASS | Existing declarations and verifiers remain authoritative; analysis cells do not redefine outcomes or artifact validity. |
| II. Honest Conformance | PASS | Baselines are labeled exploratory, dataset-specific diagnostics; synthetic and censored evidence boundaries are displayed, with no efficacy or pooled cross-family claims. |
| III. Contract-First Testing | PASS | Analysis helpers receive focused tests for split, leakage, support, alignment, and censoring edge cases; verifier semantics remain covered by existing tests. |
| IV. Deterministic Core, Explicit Effects | PASS | Fixed seeds/splits and explicit local files; no network or input mutation. Large MetroPT-3 input is streamed. |
| V. Minimal Reference Scope | PASS | Analysis remains notebook-only and optional; no base dependency or published package/API growth. |
| Development Workflow | PASS | Spec Kit artifacts updated; dependency and execution workflows use the uv lock; unrelated dirty work is preserved. |

## Research Decisions

See [research.md](research.md). Dataset methods and their limits are grounded in the repository-pinned manifests and linked primary source records.

## Data Model

See [data-model.md](data-model.md). The work adds only in-memory, read-only analysis products.

## Project Structure

```text
notebooks/
├── README.md
├── _support.py
├── _analysis.py
├── 00_outcome_commensurability.ipynb
├── 01_ai4i2020.ipynb
├── 02_apachejit.ipynb
├── 03_nasa_cmapss.ipynb
└── 04_metropt3.ipynb

tests/test_notebook_analysis.py
tests/test_notebook_support.py
scripts/check_notebooks.py
```

**Structure Decision**: Keep notebook setup, verifier gating, and chart rendering in the existing notebook support seam. Put only deterministic, reusable analysis primitives in `notebooks/_analysis.py` so they can be tested without public data. Keep dataset-specific narrative, plots, feature lists, and model pipelines visible in notebook cells. Do not add functionality to `isoprax/` or duplicate verification logic.

## Quickstart

See [quickstart.md](quickstart.md) for the locked launch, local data layout, analyses, and headless checks.

## Complexity Tracking

No constitution violations or persistent data model are introduced. The optional pandas dependency is limited to the notebook extra to support readable tabular exploration and chunked processing of MetroPT-3.
