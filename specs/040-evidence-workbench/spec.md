# Feature Specification: Local Evidence Review Workbench

**Feature Branch**: `codex/local-evidence-workbench`

**Created**: 2026-09-22

**Status**: Implemented; public-dataset artifacts remain user-supplied

**Input**: User description: "Add a local graphical workbench that makes Isoprax's examples, verification outputs, and graphs easier to review; include a quick visual signal when something may be wrong."

## User Scenarios & Testing

### User Story 1 - Get oriented and try the synthetic demo (Priority: P1)

A researcher or reviewer opens the workbench and quickly understands what the repository demonstrates, what evidence each public-data example contains, and what claims it does not support. They can run the existing synthetic cross-family demo without downloading any dataset.

**Why this priority**: First-time users need an immediate, safe way to see the project's value without first learning its command-line workflow or mistaking synthetic evidence for public-data validation.

**Independent Test**: Start the workbench with no public datasets available, view all four example descriptions and claim boundaries, run the existing synthetic demo, and confirm that no public-data verification is reported as having run.

**Acceptance Scenarios**:

1. **Given** no public dataset files are available, **when** a user opens the workbench, **then** all four examples, their evidence classes, their distinct outcomes, and their claim boundaries are visible.
2. **Given** a user has not selected a dataset, **when** they run the synthetic demo, **then** its output is labeled synthetic and separate from public-dataset verification.
3. **Given** the workbench is started without network access, **when** the user views the orientation and demo, **then** the workbench remains usable and does not try to download data.

### User Story 2 - Verify local dataset artifacts (Priority: P1)

A researcher supplies paths to local artifacts for AI4I 2020, ApacheJIT, NASA C-MAPSS, or MetroPT-3 and runs the corresponding existing verifier. The workbench presents the result and enough provenance and diagnostics to review it without hiding errors or warnings.

**Why this priority**: The repository's concrete value includes repeatable checks against distinct public-data examples; a guided path removes friction while preserving the existing verifier as the authority.

**Independent Test**: Use valid and malformed local fixtures for each verifier, including the required C-MAPSS train/test/RUL files and MetroPT-3 interval manifest, and confirm the workbench reports the verifier's result without changing input files.

**Acceptance Scenarios**:

1. **Given** valid local artifacts and required auxiliary files, **when** the user runs the matching verifier, **then** the workbench shows verified status, artifact identity, observed counts, warnings, and dataset-specific diagnostics.
2. **Given** a missing path, malformed artifact, missing C-MAPSS companion file, or invalid MetroPT-3 anchor manifest, **when** the user runs verification, **then** the workbench shows an unavailable or failed state with the relevant message and remains usable.
3. **Given** a verifier has not been run, **when** the user views its page, **then** the status is shown as not run or unavailable, never as verified or as a zero-valued result.
4. **Given** a public dataset is selected, **when** the user supplies a web URL instead of a local path, **then** the workbench does not fetch it and explains that local artifacts are required.

### User Story 3 - Review evidence with dataset-specific graphs (Priority: P1)

A reviewer uses plots and concise status cues to notice unusual counts, distributions, coverage, or verifier diagnostics. Every graph is tied to one dataset, one outcome definition, and a named local or pinned-snapshot source.

**Why this priority**: Visual summaries make structural problems and label semantics easier to spot than raw tables, while dataset-specific views prevent a visual layer from implying that unlike outcomes can be pooled.

**Independent Test**: Verify representative fixtures for each dataset and compare each rendered chart's values and labels to the verifier report; confirm errors, warnings, censoring, and claim boundaries remain visible.

**Acceptance Scenarios**:

1. **Given** a verified AI4I artifact, **when** the reviewer opens its results, **then** composite and mode-label counts, multi-mode rows, and label discrepancies are shown without implying the mode counts are mutually exclusive.
2. **Given** a verified ApacheJIT artifact, **when** the reviewer opens its results, **then** per-project positive yield and project volume are reviewable, including projects with zero positives.
3. **Given** a verified C-MAPSS subset, **when** the reviewer opens its results, **then** train/test unit and row counts plus RUL alignment are visible as subset-specific evidence.
4. **Given** a verified MetroPT-3 artifact and interval manifest, **when** the reviewer opens its results, **then** coverage by external anchor and observed cadence are graphed, and observations outside anchors remain visibly censored rather than labeled negative.
5. **Given** any dataset page, **when** the user reviews its graphs, **then** a verifier error or warning is also surfaced in text and status indicators; color is not the sole carrier of meaning.
6. **Given** results from multiple datasets, **when** the user navigates between them, **then** no pooled score, shared ranking, or cross-family aggregate chart is presented.

### User Story 4 - Review repository test and architecture signals (Priority: P2)

A maintainer explicitly runs the bounded test-and-coverage gate and reviews its current result and module coverage graph. The maintainer can also inspect a bounded neighborhood of the generated Graphify code graph when that artifact is present.

**Why this priority**: The same local workbench can provide the human-review “eye” requested for test and graph outputs, but these engineering signals must remain distinct from evidence about dataset behavior or predictive efficacy.

**Independent Test**: Run the allowed local coverage gate successfully and with a controlled failure, load a valid bounded Graphify fixture and an absent or stale graph, and confirm the workbench distinguishes pass, fail, and unknown without executing arbitrary commands or regenerating Graphify output.

**Acceptance Scenarios**:

1. **Given** a maintainer explicitly requests the repository test/coverage gate, **when** it completes, **then** the workbench displays its exit status and bounded command output and graphs per-module branch-aware coverage against the repository's declared threshold.
2. **Given** no test gate was run in the current workbench session, **when** an older coverage artifact exists, **then** it is labeled as a prior artifact with its timestamp and is not represented as a current test pass.
3. **Given** a valid Graphify graph artifact exists, **when** the maintainer searches for a node, **then** the workbench displays a bounded, readable neighborhood and the graph's recorded build identity.
4. **Given** the Graphify artifact is missing, malformed, or does not match the checked-out source identity, **when** the maintainer opens the architecture view, **then** the view reports unavailable or potentially stale and does not treat that state as a test failure or pass.
5. **Given** the maintainer opens repository review, **when** they do not explicitly request a check, **then** no tests, Graphify builds, network operations, or repository mutations are started.

### Edge Cases

- A path is empty, unreadable, a directory, or names a URL instead of a local file; display an actionable error without attempting network access. Readable local files may be outside the repository.
- One of the C-MAPSS companion files is absent or belongs to a different subset; show the verifier's result and do not chart unverified values as valid evidence.
- A MetroPT-3 interval manifest is absent, malformed, timezone-qualified, or has no matching observations; preserve the verifier's failure and censoring semantics.
- A report is valid but has warnings; show verified status and warnings together instead of hiding one behind the other.
- An input is too large for an interactive raw-row table; show bounded report summaries and charts without loading the complete dataset into a second in-memory copy.
- Coverage or Graphify output is absent, unreadable, malformed, or stale; report unknown/unavailable, not zero, green, or failed.
- The test/coverage command exceeds its time limit or cannot start; preserve a clear incomplete state and bounded diagnostic output.
- Labels, paths, graph node identifiers, or report strings contain markup or control characters; render them as data, not executable content.

## Requirements

### Functional Requirements

- **FR-001**: The workbench MUST provide a documented local graphical entry point for researchers and maintainers.
- **FR-002**: The workbench MUST operate locally and offline by default; it MUST NOT upload, download, or follow URLs for dataset artifacts.
- **FR-003**: The workbench MUST explain the evidence class, outcome semantics, source identity, and claim boundary for AI4I 2020, ApacheJIT, NASA C-MAPSS, and MetroPT-3 before presenting results.
- **FR-004**: The workbench MUST invoke the existing dataset verifier logic for each example rather than implement parallel structural or provenance rules.
- **FR-005**: The workbench MUST distinguish not-run/unavailable, verified-with-warnings, and failed states, and MUST preserve the verifier's errors, warnings, observed values, artifact identity, and claim boundary.
- **FR-006**: The workbench MUST keep the existing synthetic demo visibly separate from public-data verification and MUST label its evidence as synthetic.
- **FR-007**: The workbench MUST provide dataset-specific graphs for the counts and diagnostics specified by the acceptance scenarios, with readable titles, labels, and source context.
- **FR-008**: Graphs MUST NOT pool, rank, or aggregate outcomes across distinct datasets or present structural verification as predictive efficacy, production validation, Semantic Conformance, or Full Conformance.
- **FR-009**: MetroPT-3 visualizations MUST show external-anchor coverage and observed cadence without converting uncovered or censored observations into negative labels.
- **FR-010**: The repository review view MUST run only an explicit, fixed local test/coverage action; it MUST NOT accept or execute user-supplied shell commands.
- **FR-011**: The repository review view MUST distinguish a check executed in the current session from a previously generated coverage artifact and MUST show the artifact's age or report unknown when freshness cannot be established.
- **FR-012**: When valid Graphify output exists, the repository review view MUST allow inspection of a bounded code-graph neighborhood and show its recorded source/build identity; absent, malformed, or mismatched output MUST be reported as unavailable or potentially stale.
- **FR-013**: The workbench MUST NOT automatically run or regenerate Graphify output, run network-enabled audit/deployment operations, modify source artifacts, or persist selected local paths beyond the active session.
- **FR-014**: Status and warnings MUST be understandable without relying on color alone and MUST provide a text explanation for every visual warning state.
- **FR-015**: The workbench MUST present no dataset chart from a failed or unavailable verification as if it described a verified input; any pinned snapshot overview MUST be explicitly labeled as recorded reference data, not a current local run.

### Key Entities

- **Example**: One of the four public-data cases, with its evidence class, distinct outcome definition, source, verifier, and claim boundary.
- **Local Artifact Set**: Explicit local paths for the files required by one example; C-MAPSS and MetroPT-3 have multiple required artifacts.
- **Verification Report**: The existing verifier's identity, observed values, diagnostics, warnings, errors, status, and claim boundary.
- **Evidence Graph**: A dataset-specific plot whose values are traceable to a verification report or explicitly labeled pinned snapshot.
- **Repository Check Run**: One explicit test/coverage invocation with status, output, and associated coverage artifact identity/time.
- **Architecture Graph Snapshot**: Optional Graphify output tied to a recorded source/build identity; it is not dataset evidence or a conformance result.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A first-time reviewer can locate all four examples, identify their distinct evidence classes, and start the synthetic demo from the documented local entry point in under three minutes after environment setup.
- **SC-002**: For valid and malformed local fixtures of all four examples, the workbench shows the same verification outcome and diagnostics as the existing verifier, with no unhandled UI error.
- **SC-003**: Every example has at least one graph matching its verifier-derived values, and automated tests detect any mismatch between report values and plotted data.
- **SC-004**: A reviewer can distinguish a failed verification, a verified report with warnings, an unrun verifier, and a missing/stale repository artifact without relying on color alone.
- **SC-005**: No displayed dataset graph combines outcomes from different examples, and MetroPT-3 observations outside declared anchors remain censored in every view.
- **SC-006**: The repository review view reports a controlled test/coverage pass and failure accurately, and never marks a prior or unavailable artifact as a current pass.
- **SC-007**: With a Graphify artifact of the repository's current size, a maintainer can search for a node and view a bounded neighborhood without rendering the entire graph into an unreadable page.
- **SC-008**: A network-disabled run can open the workbench, view the demo, and verify local fixtures; user-supplied dataset contents and paths are not sent to an external service.

## Assumptions

- The primary audience is a local researcher, reviewer, or maintainer working from a repository checkout with Python and `uv` available.
- The user means both dataset evidence charts and the existing Graphify code graph; these belong in separate views and have different meanings.
- Public datasets remain user-supplied local files; the workbench does not vendor or automatically retrieve them.
- Repository test/coverage execution is opt-in and limited to the existing local coverage gate; deployment, dependency audit, and Graphify generation remain outside the UI.
- A missing or stale graph/coverage artifact is an unknown state, not a positive or negative quality result.
- Charts are review aids derived from declared verifier outputs; they do not implement a new anomaly detector or predictive model.
