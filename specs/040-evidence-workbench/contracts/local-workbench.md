# Local Workbench Contract

## Runtime

- The workbench is an optional local tool started from a repository checkout.
- It binds to loopback (`127.0.0.1`), disables usage statistics, and requires no remote service.
- Public artifact inputs are filesystem paths only. The app does not accept URLs, upload file contents, persist paths, or mutate artifacts.
- Missing UI dependencies produce a setup instruction; missing datasets, coverage, or Graphify output remain distinct unavailable states.

## Dataset Verification

The UI calls the existing verifier functions and preserves each native report. C-MAPSS requires all three files and a selected subset. MetroPT-3 uses the same interval-manifest parser as the existing CLI. Reports retain the original `verified`, `artifact`, `observed`, `diagnostics`, `errors`, `warnings`, and claim-boundary fields where provided.

Presentation states are `not_run`, `verified`, `verified_with_warnings`, `failed`, and `unavailable`. Only the two verified states expose report-derived dataset charts. The raw report remains inspectable as structured data.

## Chart Data

Chart values come from the just-returned verifier report, not from hard-coded expected counts. The charts are distinct by example:

- AI4I composite/mode counts and discrepancy summaries.
- ApacheJIT project positive yields and project volumes.
- C-MAPSS subset row/unit counts and test-unit/RUL alignment.
- MetroPT-3 per-anchor coverage and observed timestamp-gap frequencies.

All charts have human-readable titles, labels, evidence class/source, and nearby warning text. No chart pools labels, scores, or counts across examples. MetroPT-3 has no inferred negatives outside explicit anchors.

## Explicit Local Actions

Only named actions are executable from the UI:

1. Run the existing synthetic demo (`uv run python examples/demo_cross_family.py`).
2. Run the existing test and branch-coverage gate (`make coverage`).

Commands run with argument arrays and repository cwd, not through user-provided shell text. The test action has a 600-second timeout and captured output is truncated to the last 20,000 characters. No dependency audit, deployment, Graphify generation/update, or other command is callable from the UI.

The current-session test status exists only in session state. A preexisting `coverage.json` is displayed separately with timestamp and branch-coverage metadata. A module chart is not labeled as a current pass unless the current-session gate succeeds.

## Graphify View

The app reads `graphify-out/graph.json` only if present. It requires a JSON object with node and link arrays and valid IDs/labels/endpoints. It displays the recorded build commit and warns when the commit differs from current HEAD, worktree changes are detected, or provenance is unavailable.

Search results render at most 60 nodes and 200 links around a deterministic matching start node. IDs and labels are quoted as data in Graphviz source. The generated `graph.html` is never embedded or executed. Unsupported, absent, or stale data is reported without a green/red quality judgment.

## Error Handling

- Empty, invalid, or URL paths produce inline actionable messages.
- Verifier exceptions are converted into `unavailable` with a sanitized message; verifier errors remain `failed` and warnings remain visible.
- Invalid report projections are omitted and diagnosed; no default zero chart is drawn.
- Command missing/timeout/nonzero exit is shown as unavailable/timed out/failed with bounded output.
- Invalid coverage or Graphify JSON yields an unavailable report with a reason, not an application crash.
