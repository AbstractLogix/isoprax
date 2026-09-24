# Data Model: Guided Research Notebooks

The feature adds no persistent application entities, database tables, or public Isoprax APIs. Notebook outputs exist only in memory.

## Verified Dataset Review

- **Dataset ID**: `ai4i2020`, `apachejit`, `cmapss`, or `metropt3`.
- **Input paths**: Explicit local files; C-MAPSS requires one matching train/test/RUL triplet, MetroPT-3 requires the tracked external-interval manifest.
- **Verification state**: `not_run`, `unavailable`, `failed`, `verified`, or `verified_with_warnings` from the current workbench adapter.
- **Artifact identity and report**: The verifier's hashes, observed counts, diagnostics, warnings/errors, and claim boundary.
- **Analysis gate**: Only `verified` / `verified_with_warnings` permits reading rows for exploration. Other states return no data-derived tables, plots, or metrics.

## Exploratory Analysis

- **Audit**: Dataset-local counts and label/source diagnostics from the verified local file.
- **Visualization**: Read-only descriptive plots with labels and units appropriate to that family.
- **Baseline split**: A deterministic dataset-specific held-out partition, separate from any cross-family comparison.
- **Metric**: A dataset-local result with explicit train/test support and a not-estimable reason when prerequisites are absent.

### Dataset-Specific Evaluation Records

- **AI4I 2020**: Ordered UDI holdout. Features exclude both identifiers and all outcome/mode-label columns. Outcome is the composite `Machine failure`; mode columns are used only for prevalence/overlap analysis. Evidence remains synthetic.
- **ApacheJIT**: UTC `author_date` cutoff at 2017-01-01. Train uses earlier rows; test uses later rows. Only the 12 commit metrics are predictors. `buggy` is the target; `fix`, identifiers, project, and date/year fields are excluded. Results use the pinned full-total artifact and are not identical to the release's balanced train subset.
- **NASA C-MAPSS**: One analysis per FD subset. Training RUL is derived within each run-to-failure train unit; test features are the final observed row per test unit, targets are the supplied test RUL vector. Unit ID is not a model feature. No cross-subset aggregate is produced.
- **MetroPT-3**: Time-series summary from bounded input chunks: count-weighted hourly means for the stream and minute means inside bounded anchor-context windows. The cadence summary comes from verifier-observed adjacent timestamp gaps. Reported intervals alone are shaded; rows outside remain censored/unlabeled. No binary confusion matrix or supervised score exists.

## Metric Semantics

- Classification: prevalence, average precision, ROC-AUC when both classes appear in test, Brier score, fixed-threshold confusion table, and explicit sample counts.
- Regression: MAE, RMSE, and test-unit count.
- Undefined metrics are represented as not estimable with a reason, never as numeric zero.
- Every result is an exploratory, dataset-local baseline and does not constitute an Isoprax efficacy, conformance, or production claim.
