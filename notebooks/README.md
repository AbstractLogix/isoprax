# Isoprax research notebooks

These notebooks provide a portable, human-reviewable view of the dataset
examples and their outcome boundaries. They reuse Isoprax's structured
comparator, local verifiers, and report chart projections. Notebook cells do
not fetch, upload, modify, or vendor dataset artifacts. The first isolated
environment creation may retrieve the locked Python packages.

## Install and launch

The standard launch uses the optional `notebooks` extra from `uv.lock` in a
temporary isolated environment. JupyterLab and its `python3` kernel therefore
share the same dependency set and checked-out Isoprax source, without syncing or
removing packages from the project's shared `.venv`:

```bash
make notebooks
```

The notebook metadata uses the standard `python3` kernel. The launch command
selects the isolated repository environment automatically. For PowerShell or
when running without Make, use the equivalent locked command directly:

```powershell
$env:ISOPRAX_DATA_DIR = 'D:\research data'
uv run --isolated --locked --no-default-groups --extra notebooks jupyter lab notebooks/ --ip=127.0.0.1
```

The notebooks display the active Python executable and reject a
repository/kernel mismatch.

CI executes notebooks on Ubuntu with Python 3.10, 3.12, and 3.14, and on
Windows with Python 3.12. The optional `notebooks` extra is lockfile-backed
and does not add Jupyter dependencies to the base Isoprax installation.

## Local dataset files

By default, notebooks look under the ignored `<checkout>/data/` directory.
Set `ISOPRAX_DATA_DIR` before launching Jupyter to use another absolute or
checkout-relative directory; paths containing spaces and platform-native path
separators are supported. Each notebook also exposes a path cell that can be
edited for a custom layout.

On POSIX shells, set a custom path when launching with
`ISOPRAX_DATA_DIR='/mnt/research data' make notebooks`.

```text
data/
├── ai4i2020.csv
├── apachejit_total.csv
├── cmapss/
│   ├── train_FD001.txt
│   ├── test_FD001.txt
│   └── RUL_FD001.txt
└── MetroPT-3(AirCompressor).csv
```

The C-MAPSS notebook expects all three files for each subset FD001–FD004.
MetroPT-3 uses the tracked `examples/metropt3/failure_intervals.json` anchor
manifest. The verifiers require the expected source files and report malformed
or incomplete inputs. Missing files are reported as `not_run`, with the
expected paths; no missing value is converted to zero and no download is
attempted.

## Notebook guide and evidence limits

- `00_outcome_commensurability.ipynb` compares the declared AI4I composite
  failure, ApacheJIT buggy-commit, C-MAPSS remaining-useful-life, and MetroPT-3
  externally anchored air-leak outcomes. Its matrix comes from the structured
  comparator. It displays no pooled score or empirical efficacy result.
- `01_ai4i2020.ipynb` audits composite/mode prevalence and overlap, plots
  feature distributions, then compares a prior-only classifier with logistic
  regression on an ordered 80/20 UDI split. IDs and all mode labels are excluded
  from predictors. UDI is only an ordering key, not a production-time claim.
  AI4I is synthetic; a structural pass is not predictive efficacy.
- `02_apachejit.ipynb` audits per-project and per-UTC-year label yield (including
  zero-positive projects) and source-year mismatches. It compares a prior-only
  classifier with logistic regression on the 12 commit metrics, using
  `author_date < 2017-01-01 UTC` for training and later commits for test.
  Project, IDs, labels, year, and timestamp are excluded from predictors. These
  are repository-derived buggy-commit labels, not runtime failures.
- `03_nasa_cmapss.ipynb` shows training engine lifetimes and example sensor
  trajectories, derives training RUL within each engine, and compares a
  training-median baseline with fixed histogram gradient boosting on each
  subset's official test RUL targets. Only final test rows are scored; FD001–
  FD004 results stay separate. C-MAPSS is simulated run-to-failure data.
- `04_metropt3.ipynb` measures adjacent timestamp gaps, plots chunk-reduced
  hourly stream means, and shows minute-mean context windows around externally
  reported intervals. The six-hour margins are visual context, not expanded
  labels; observations outside the reported intervals remain censored, not
  negative. It deliberately reports no supervised score.

Verifier report charts remain available for verified or verified-with-warnings
artifacts. Raw-row exploration is also gated by that successful verification;
failed, unavailable, or missing-input results remain visible without success
plots or scores. Classification tables include support, prevalence, average
precision, supported ROC-AUC, Brier score, and a fixed 0.5-threshold confusion
table; regression tables include test support, MAE, and RMSE. These are fixed,
single-pass baselines, not tuned models. None of these notebooks establishes Semantic/Full
Conformance, predictive efficacy, or production performance, and outcomes
from different families are not pooled.

## Headless validation

Run the same notebook sources used in CI in a temporary isolated environment,
without changing the shared project environment or writing outputs into the
checked-in files:

```bash
make notebook-check
```

This validates notebook schema and kernel metadata, rejects saved outputs,
execution counts, and machine-specific source paths, then executes each
notebook in memory. Dataset notebooks should show `not_run` when the local
files above are absent.
