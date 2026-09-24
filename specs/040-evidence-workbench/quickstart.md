# Quickstart: Local Evidence Review Workbench

The workbench is optional and local-only. It does not download or vendor data. The four examples remain distinct evidence cases and none of their structural checks establish predictive efficacy or cross-family pooling.

## Install and start

```bash
make workbench
```

The target resolves the locked optional UI dependency without selecting the
development dependency group. Open the loopback URL printed by Streamlit. The
app is bound to `127.0.0.1`; browser usage statistics are disabled.

With no dataset files present, the app still explains AI4I 2020, ApacheJIT, NASA C-MAPSS, and MetroPT-3, and can run the existing synthetic demo. That demo is not public-data validation.

## Verify local files

Choose the example and provide local paths in the UI:

- AI4I 2020: one CSV.
- ApacheJIT: one CSV.
- NASA C-MAPSS: select FD001–FD004 and provide train, test, and RUL files for that subset.
- MetroPT-3: one CSV and an interval manifest; the checked-in `examples/metropt3/failure_intervals.json` can be selected for the pinned UCI anchors.

The app displays the original verifier report and only draws report-derived charts after a successful verification. On failure, inspect the verifier's text errors; no chart is presented as verified evidence. Charts are separate per example and preserve each dataset's outcome and censoring caveats.

## Review graphs and repository health

- Dataset charts show only within-example counts/diagnostics. MetroPT-3 uncovered observations remain censored.
- The Repository Review view runs `make coverage` only after an explicit click. It does not run `make check`, dependency audit, or deployment actions.
- A prior `coverage.json` is shown with its timestamp; it is not a current pass. The current test result is separate, and modules without reported coverage stay unknown.
- If `graphify-out/graph.json` exists, search for a symbol to view a one-hop neighborhood capped at 60 nodes and 200 links. The app does not build or update Graphify; absent, malformed, or mismatched output is labeled unavailable or potentially stale.

## Verify the feature

```bash
uv run pytest -o addopts= tests/test_workbench_datasets.py tests/test_workbench_repository.py -q
make coverage
make lint
make format-check
make workbench
```

The base test suite does not require the optional workbench dependency. The
workbench's pure helpers are testable without Streamlit; the headless UI smoke
test is performed with the optional `workbench` extra installed.
