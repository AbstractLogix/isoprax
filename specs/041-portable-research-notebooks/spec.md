# Feature Specification: Guided Research Notebooks

**Feature Branch**: `codex/local-evidence-workbench`

**Created**: 2026-09-22

**Status**: Implemented; exact-corpus analysis and hosted platform CI remain pending

**Input**: User request: expand the portable Jupyter notebook set into useful, dataset-specific Isoprax research examples, with baseline analysis only where the data and split support it.

## User Scenarios & Testing

### User Story 1 - Understand outcome boundaries (Priority: P1)

A researcher can inspect the declared outcomes for AI4I 2020, ApacheJIT, NASA C-MAPSS, and MetroPT-3, compare them with Isoprax's structured comparator, and see why visually similar labels do not automatically permit pooled results.

**Independent Test**: Run the outcome notebook without dataset files or network access; it displays each definition, all pairwise comparison levels, differing fields, and pooling decisions, with no pooled empirical metric.

**Acceptance Scenarios**:

1. **Given** no public datasets are installed, **when** the researcher runs the overview, **then** outcome definitions and comparator results render from repository declarations alone.
2. **Given** two definitions differ, **when** they are compared, **then** the differing fields and comparator's pooling decision are visible and calibration is not presented as a repair for mismatched outcomes.

### User Story 2 - Investigate one dataset with evidence-aware analysis (Priority: P1)

A researcher can configure a local artifact, review its authoritative Isoprax verification report, explore the observed data and labels with meaningful dataset-specific tables and plots, and run a small, disclosed baseline only where the label and evaluation design support it.

**Why this priority**: A verifier summary is useful for admission, but not sufficient for a research example. The notebooks must show what can actually be learned from each corpus and where its evidence stops.

**Independent Test**: With no files configured, each notebook reports `not_run` and skips all data analysis. With locally supplied verified files, it renders the dataset-specific audit and analysis below. With invalid files, it displays verifier diagnostics and skips success charts and baseline evaluation.

**Acceptance Scenarios**:

1. **Given** an input is absent or verification fails, **when** a dataset notebook runs, **then** it reports the state and diagnostics and does not read, plot, or score the artifact as valid evidence.
2. **Given** AI4I 2020 verifies, **when** its notebook runs, **then** the researcher sees composite/mode prevalence, mode overlap and discrepancies, feature distributions, and a simple composite-failure baseline using an ordered-UDI holdout. Identifiers and all mode-label columns are excluded from model inputs; the notebook labels results as exploratory evidence on synthetic data.
3. **Given** ApacheJIT verifies, **when** its notebook runs, **then** it shows class prevalence and project/year label yield, uses commit metrics only, and evaluates a simple baseline on a deterministic chronological holdout formed from `author_date`. It reports the cutoff and test support, distinguishes this full-dataset split from the release's separately distributed balanced training subset, and labels the target as repository-derived bug-inducing commits rather than operational failures.
4. **Given** one or more C-MAPSS subsets verify, **when** their notebook runs, **then** it shows per-subset unit lifetimes, RUL alignment, and example sensor trajectories; derives training RUL only from run-to-failure training units; and compares a simple regressor with a fixed training-median baseline on official test-unit RUL at each unit's final observed cycle. Results stay separated by FD subset.
5. **Given** MetroPT-3 verifies with its external interval manifest, **when** its notebook runs, **then** it shows a resource-bounded time-series summary and sensor views around the four reported intervals, visibly distinguishes anchored intervals from censored observations, and does not train or score a supervised failure predictor from the sparse interval anchors.
6. **Given** a metric cannot be estimated because its evaluation partition lacks required class support or valid targets, **when** the results are shown, **then** that metric is labeled not estimable with the reason rather than replaced with zero.

### User Story 3 - Run the same notebook environment across supported setups (Priority: P1)

A researcher follows one documented launch and data-path convention and can execute the notebooks in the locked repository environment across supported operating systems and Python versions.

**Independent Test**: In a fresh checkout without benchmark data or network access, execute all notebooks headlessly on each CI Python/platform target; confirm no uncaught errors, network activity, saved outputs, or machine-specific source paths.

**Acceptance Scenarios**:

1. **Given** a supported Python installation and the repository lockfile, **when** the researcher follows the quickstart, **then** the kernel imports this checkout and resolves local data without machine-specific path edits.
2. **Given** notebooks execute in CI, **when** all cells finish, **then** errors fail the check while outputs and execution counts remain absent from committed notebooks.
3. **Given** required local files are missing, **when** CI executes the notebooks, **then** they skip data-dependent analysis without downloading, fabricating benchmark records, or changing shared environment state.

## Edge Cases

- A configured path contains spaces, non-ASCII characters, or platform-specific separators.
- A notebook kernel imports another checkout or a different Isoprax environment.
- A required artifact is absent, unreadable, malformed, hash-mismatched, or paired with the wrong C-MAPSS subset.
- A held-out classification partition contains only one class; ROC-AUC is not estimable.
- An ApacheJIT timestamp is inconsistent with the separate `year` field; the split uses parsed `author_date` and surfaces the verifier's mismatch count.
- C-MAPSS unit identifiers repeat between train and test files; the files are treated as separate official populations and RUL is aligned by test-file unit order as verified by the existing adapter.
- MetroPT-3 contains long gaps or irregular cadence; observed cadence is reported, never silently normalized.
- MetroPT-3 has observations outside the externally reported failure intervals; they remain censored rather than becoming negative labels.
- An input verifies with warnings; the warnings and limitations remain visible beside all derived analysis.

## Functional Requirements

- **FR-001**: Provide one offline notebook showing the repository-declared outcome definitions and every displayed pairwise structured commensurability result.
- **FR-002**: Provide one separate dataset notebook each for AI4I 2020, ApacheJIT, NASA C-MAPSS, and MetroPT-3.
- **FR-003**: Dataset notebooks MUST call the existing verifier before reading an artifact for analysis. They MUST reuse repository paths and outcome/anchor declarations rather than duplicate verification, provenance, or censoring rules.
- **FR-004**: Dataset files MUST be user-supplied local inputs. Notebook code MUST NOT download, upload, overwrite, or vendor them.
- **FR-005**: Missing inputs MUST be reported as `not_run`; missing evidence MUST NOT be represented as a zero count, negative outcome, or successful verification.
- **FR-006**: Each dataset notebook MUST display verification status, artifact identity, observed values, diagnostics, warnings/errors, and claim boundary before derived analysis.
- **FR-007**: Data-derived charts and baseline results MUST run only when the matching artifact verification is successful. Failed/unavailable/not-run states MUST remain visible without success analysis.
- **FR-008**: Cross-family comparison MUST be limited to declared definitions and structured comparator results. No pooled cross-family metrics, rankings, or efficacy claims are allowed; C-MAPSS subsets are also reported independently.
- **FR-009**: The optional notebook environment MUST be lockfile-backed, documented, and usable on supported Python versions without hard-coded machine paths or changes to the base dependency set.
- **FR-010**: Headless execution MUST validate notebook schema and kernel metadata, fail on cell errors, and leave committed outputs and execution counts empty.
- **FR-011**: Every notebook MUST state evidence class, required local inputs, and claim boundary before showing derived results.
- **FR-012**: Each dataset notebook MUST include a readable data/label audit and at least one domain-relevant plot beyond verifier summary counts.
- **FR-013**: AI4I 2020 MUST analyze class prevalence, failure-mode overlap/discrepancies, and feature distributions. Its composite-failure baseline MUST use an ordered-UDI holdout and MUST exclude identifiers and failure-mode label columns from predictors.
- **FR-014**: ApacheJIT MUST analyze label yield by project and time and provide a simple classifier diagnostic on a deterministic author-time holdout. Predictors MUST be limited to commit metrics; identifiers, label fields, project, and date fields MUST not enter the model. The custom split and estimand MUST be disclosed.
- **FR-015**: C-MAPSS MUST visualize unit/trajectory structure and independently evaluate a simple RUL baseline per subset. Training RUL may be derived from training trajectories that end at failure; test RUL MUST come from the matching official RUL file and be aligned to final observed test rows.
- **FR-016**: MetroPT-3 MUST provide memory-bounded time-series exploration and display the declared external intervals. It MUST retain censored/unobserved status outside intervals and MUST NOT present supervised metrics from the interval-only labels.
- **FR-017**: Baselines MUST be fixed, transparent, and evaluated once on declared held-out data without tuning against the reported test results. Classification and regression metrics MUST be named and not estimable values handled explicitly.
- **FR-018**: Notebook analysis helpers MUST have focused automated tests using clearly synthetic fixtures; fixture outputs MUST NOT be described as public-dataset evidence.

## Key Entities

- **Outcome Definition**: The event, observation process, window, thresholds, and description compared by Isoprax.
- **Dataset Review**: A verified local artifact and its report, diagnostics, identity, and claim boundary.
- **Exploratory Analysis**: Read-only summaries/plots computed from a successfully verified local artifact.
- **Baseline Evaluation**: A fixed simple model and explicit train/test split for one dataset outcome, with metrics and support counts; never a cross-family result.
- **Censored Observation**: A row without an outcome label under the declared observation process, especially MetroPT-3 rows outside reported intervals.
- **Notebook Environment**: The optional locked dependency and kernel context used to execute repository notebooks.

## Success Criteria

- **SC-001**: All five notebooks execute without uncaught errors in a fresh checkout with no benchmark data and no network access.
- **SC-002**: For each verified local dataset artifact, its notebook renders a data/label audit, at least one dataset-specific visualization, and the verifier report; missing or failed artifacts produce no data-dependent analysis.
- **SC-003**: The outcome overview shows comparator results for every displayed pair and no pooled empirical score.
- **SC-004**: AI4I, ApacheJIT, and each C-MAPSS subset produce deterministic, explicitly split baseline metrics when valid data are present; unsupported metrics are explicitly not estimable. MetroPT-3 presents descriptive anchored-window analysis and no supervised score.
- **SC-005**: A single documented launch/check workflow passes on Ubuntu with Python 3.10, 3.12, and 3.14 and Windows with Python 3.12.
- **SC-006**: Automated tests cover split construction, leakage exclusions, RUL alignment, censored-window handling, and missing-input gating with synthetic fixtures.
- **SC-007**: Committed notebooks contain no saved outputs, execution counts, or absolute machine-specific paths.

## Assumptions

- Researchers obtain the exact locally verified artifacts themselves. The notebooks do not replace the verifier's pinned artifact expectations.
- ApacheJIT analysis uses `author_date` from the pinned total artifact for a disclosed custom temporal holdout; the published `year` field is audit-only because verifier checks record known year/epoch mismatches.
- AI4I UDI provides an ordered holdout key but is not asserted to be production time. Its generated-data results remain synthetic and exploratory.
- The C-MAPSS train/test files represent distinct engine populations as described by NASA; the existing verifier remains authoritative for matching subset files and RUL count.
- MetroPT-3 failure intervals are sparse external reports over an otherwise unlabeled stream. They are descriptive anchors, not a complete negative/positive label series.
- Baseline metrics are methodological examples on each dataset's own declared outcome. They do not establish predictive efficacy, Semantic/Full Conformance, or real-fleet performance.
