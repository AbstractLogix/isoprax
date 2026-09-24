# Data Model: Local Evidence Review Workbench

The workbench is a local presentation adapter. Existing verifier report types remain authoritative and are not collapsed into one outcome schema.

## Example Definition

One static description of an example shown before verification.

| Field | Meaning |
|---|---|
| `dataset_id` | Stable local identifier: `ai4i2020`, `apachejit`, `cmapss`, or `metropt3`. |
| `evidence_class` | Example-specific evidence type, kept verbatim from current project documentation. |
| `outcome_summary` | What one observation/label means for this example. |
| `source_reference` | Canonical source or repository manifest reference. |
| `claim_boundary` | Exact evidence limit shown alongside results. |

## Local Artifact Set

An ephemeral set of user-selected paths. Paths are held only in active UI session state.

| Example | Required local paths |
|---|---|
| AI4I 2020 | CSV |
| ApacheJIT | CSV |
| NASA C-MAPSS | Subset ID, train file, test file, RUL file |
| MetroPT-3 | CSV and interval-manifest JSON |

URLs are rejected as inputs. Readable files outside the repository are allowed. The workbench does not copy, modify, upload, or download artifacts.

## Verification Report

The original existing verifier report remains the source of truth. The UI tracks an additional presentation state:

- `not_run`: no verifier invocation in this session.
- `verified`: verifier returned `verified == true` with no warnings.
- `verified_with_warnings`: verifier returned true and at least one warning.
- `failed`: verifier returned false and provides errors.
- `unavailable`: required input is absent/unreadable or execution could not produce a report.

Chart projections are available only for `verified` and `verified_with_warnings`. Errors and warnings remain visible as text. `observed`, `diagnostics`, artifact identity, and `claim_boundary` are presented without changing their meanings.

## Dataset-Specific Chart Projections

- **AI4I**: counts for composite failure and five mode labels; multi-mode, failure-without-mode, mode-without-failure, and composite discrepancy metrics. Mode counts may overlap and MUST NOT be stacked as mutually exclusive classes.
- **ApacheJIT**: project positive yield and project commit count, including zero-yield projects.
- **C-MAPSS**: train/test row counts and unit counts; test-unit count versus RUL-entry count for the selected subset.
- **MetroPT-3**: observed row coverage per external interval and the verifier's timestamp-gap frequency distribution. Uncovered rows are not represented as negative examples.

Each projection includes `dataset_id`, title, x/y labels with units where applicable, and a reference to the source report. There is no shared chart projection for outcomes across datasets.

## Repository Check Run

One explicit `make coverage` execution tracked in Streamlit session state: action name, start/end time, status (`running`, `passed`, `failed`, `timed_out`, `unavailable`), exit code if present, and captured output truncated to a fixed maximum. No arbitrary command text is accepted. A prior `coverage.json` is a separate report artifact with path, modification time, branch-coverage flag, and per-module percentages; its presence does not establish a current test result.

## Architecture Graph Snapshot

Optional generated Graphify JSON with validated node/edge records, recorded `built_at_commit`, current repository HEAD, and worktree-dirty flag where Git metadata is available. The view selects a node by label and creates a deterministic bounded neighborhood. It reports missing/unsupported/mismatched provenance as unknown or potentially stale. It is not a dataset chart, test result, or conformance claim.
