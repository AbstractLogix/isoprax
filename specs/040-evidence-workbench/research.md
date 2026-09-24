# Research: Local Evidence Review Workbench

## Decisions

### Local UI framework and chart primitives

- **Decision**: Use Streamlit only as an optional `workbench` extra. Use its native bar and line charts for dataset summaries and its Graphviz chart element for a bounded code-graph neighborhood; do not add Plotly, Altair, or a separate frontend build.
- **Rationale**: Official Streamlit installation documentation currently supports Python 3.10–3.14, matching this repository's `requires-python` range. Its chart documentation includes native bar/line charts and Graphviz rendering. The package therefore fits the existing Python environment while keeping the repository's normal installation and test dependencies unchanged.
- **Alternatives considered**: A custom HTML/JavaScript app would add a second toolchain and require a server/data contract; a desktop GUI would create a separate platform surface. Adding Plotly or Altair directly is unnecessary for the report-derived charts in scope.
- **Sources**: [Streamlit installation and supported Python versions](https://docs.streamlit.io/get-started/installation/command-line); [Streamlit chart elements](https://docs.streamlit.io/develop/api-reference/charts); [Streamlit configuration reference](https://docs.streamlit.io/develop/api-reference/configuration/config.toml).

### Local-only runtime posture

- **Decision**: Launch on `127.0.0.1`, run headless, and disable browser usage statistics in the documented Make target. Accept local paths, not browser uploads or URLs.
- **Rationale**: The repository's existing public-data interface is offline and path-based. Streamlit exposes a server address setting and a browser usage-statistics setting; explicitly setting both makes the local-only posture visible rather than relying on defaults.
- **Alternatives considered**: A shared/hosted app would require remote artifact handling, authentication, and a larger privacy/security contract, none of which the request requires.
- **Sources**: [Streamlit configuration reference](https://docs.streamlit.io/develop/api-reference/configuration/config.toml); [public-dataset quickstart](../039-public-dataset-validation/quickstart.md).

### Existing verifier/report reuse

- **Decision**: Call the four existing Python verifier functions directly. Use each report's own fields to form a distinct chart projection; show no report-derived plot unless that verifier passed.
- **Rationale**: AI4I provides mode/composite counts; ApacheJIT provides per-project yields; C-MAPSS provides subset rows, units, and RUL alignment; MetroPT-3 provides external-anchor coverage and observed cadence. The data contracts already preserve errors/warnings and claim boundaries. Reimplementing validation or forcing a shared outcome model would weaken these seams.
- **Alternatives considered**: Parsing CLI text would be brittle; pooling the reports into one shared score would be semantically invalid.
- **Sources**: [Feature 038 AI4I verifier](../../isoprax/ai4i2020.py); [Feature 039 quickstart and report contract](../039-public-dataset-validation/quickstart.md), [verification report contract](../039-public-dataset-validation/contracts/verification-report.md).

### Repository review actions and outputs

- **Decision**: Add one explicit test/coverage button that runs the existing `make coverage` target, and an optional Graphify view that reads the generated JSON only. Do not run network-enabled audit or Graphify build/update commands from the app.
- **Rationale**: `make coverage` runs the project tests and per-module branch-aware threshold check; `coverage.json` carries branch-coverage metadata. Current Graphify output is generated and ignored, has a `built_at_commit`, and contains thousands of nodes, so it must be bounded and labeled by provenance. The app should never convert an absent or old artifact into a current green signal.
- **Alternatives considered**: Re-running `make check` would include dependency auditing; embedding Graphify's generated HTML would execute a script-rich artifact and create an avoidable trust problem. The JSON graph is sufficient for a capped structural neighborhood.
- **Sources**: [Makefile](../../Makefile); [module coverage gate](../../scripts/check_module_coverage.py); [Graphify CLI documentation](https://github.com/safishamsi/graphify).

## Resolved Unknowns

- The existing reports supply enough information for useful summary graphs without re-reading full datasets. This avoids a second in-memory copy of the 1.5-million-row MetroPT-3 CSV.
- The workbench is a repository-local tool; it is not installed in the published `isoprax` package.
- A test result is current only when returned by an explicit run in the current app session. A preexisting `coverage.json` remains a historical artifact with its filesystem timestamp.
- Graphify's JSON shape is treated as best-effort generated input. Missing, malformed, uncommitted, or commit-mismatched graph data yields unknown/potentially stale status, not an inferred code-quality result.
