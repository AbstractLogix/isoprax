# Quickstart: Guided Research Notebooks

The notebook set includes one outcome-comparison overview plus a research walkthrough for AI4I 2020, ApacheJIT, NASA C-MAPSS, and MetroPT-3. Dataset analyses use local read-only artifacts and stop unless the existing Isoprax verifier approves the matching files.

## Environment and launch

From the repository root:

```bash
make notebooks
```

The command uses the lockfile-backed optional notebook extra in an isolated uv environment. For a custom dataset directory, set `ISOPRAX_DATA_DIR` before launch. Without Make, launch JupyterLab with `uv run --isolated --locked --no-default-groups --extra notebooks jupyter lab notebooks/ --ip=127.0.0.1`.

## Local data layout

The default local data root is `<repository>/data`. It is ignored by Git. Researchers supply files themselves; notebook cells do not fetch data.

```text
data/
├── ai4i2020.csv
├── apachejit_total.csv
├── cmapss/
│   ├── train_FD001.txt
│   ├── test_FD001.txt
│   ├── RUL_FD001.txt
│   └── ... corresponding FD002-FD004 triplets
└── MetroPT-3(AirCompressor).csv
```

MetroPT-3 uses `examples/metropt3/failure_intervals.json`. The paths can be changed in each notebook's setup cell or by `ISOPRAX_DATA_DIR`. Every configured artifact still has to pass the pinned repository verifier; a different hash/version is not silently accepted.

## What each notebook investigates

- `00_outcome_commensurability.ipynb`: Declared events, observation processes, windows, thresholds, pairwise structured differences, and pooling decisions. No raw data or pooled score.
- `01_ai4i2020.ipynb`: Composite/mode label prevalence and overlap, feature distributions, and an ordered-UDI logistic baseline versus a prior-only baseline. Identifiers and mode labels are excluded from predictors. Findings are synthetic and exploratory.
- `02_apachejit.ipynb`: Label yield by project/time and a logistic baseline on commit metrics using a 2017-01-01 UTC author-date holdout from the pinned total artifact. It displays timestamp/year diagnostics and class support; results are about repository-derived buggy-commit labels, not operational failures.
- `03_nasa_cmapss.ipynb`: Unit lifetimes, sensor trajectories, train-derived RUL labels, and per-subset test RUL evaluation against a median baseline. Each engine subset stays separate; simulation results are not real-fleet performance.
- `04_metropt3.ipynb`: Chunked hourly sensor summary, observed sampling gaps, and minute-mean context windows around externally reported failure intervals. The six-hour margins are visualization context only. Outside-anchor observations stay censored. No supervised predictor score is reported.

## Evidence boundary

Each dataset notebook first displays verifier status, artifact hash, observed counts, diagnostics, and claim boundary. Missing or failed inputs show no success plots or metrics. Fixed baselines are single-pass methodological examples; the test partition is not used to tune the models. Undefined classification metrics are displayed as not estimable with their support reason. Outcomes and metrics remain family-specific; no cross-family score or conformance/efficacy claim is made.

## Headless validation

```bash
make notebook-check
```

This executes the same notebook cells without public artifacts, checks notebook metadata and clean outputs, and must not access the network. The no-data branch reports `not_run`. Synthetic fixture tests cover analysis-helper mechanics, not dataset evidence. CI runs the notebook checks on Ubuntu with Python 3.10, 3.12, and 3.14 and Windows with Python 3.12.
