# AI4I 2020 Verifier Contract

## Input

The CLI accepts one required path to a locally supplied `ai4i2020.csv`. It does
not download, update, or mutate the file.

## Output

The CLI emits one JSON object with:

- `verified`: boolean
- `path` and `csv_sha256`
- `row_count` and `column_count`
- `machine_failure_count` and `machine_failure_rate`
- `mode_counts`
- `multi_mode_row_count`
- `failure_without_mode_count`
- `mode_without_failure_count`
- `composite_mismatch_count`
- `errors`: deterministic invariant-failure strings
- `claim_boundary`

Exit status is zero only when `verified` is true; every other result exits
non-zero. Missing files and malformed files are reported as failed verification,
not exceptions requiring network recovery.

## No-repair rule

The verifier MUST preserve the supplied composite and mode labels. It reports
disagreement but never rewrites `Machine failure`, drops rows, or replaces mode
labels with an inferred composite.
