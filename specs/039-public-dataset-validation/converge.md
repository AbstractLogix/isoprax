# Convergence: Evidence-Bounded Dataset Examples

The example set comprises the AI4I synthetic structural/label-semantics
baseline (detailed in Feature 038) plus the ApacheJIT, C-MAPSS, and MetroPT-3
checks implemented here. Review follow-up closed four correctness/reporting gaps:
ApacheJIT now reports out-of-range epochs as validation errors; C-MAPSS rejects
fractional unit/cycle identities; MetroPT-3 preserves timezone-unqualified
date/time values, identifies the externally reported event as an air leak, and
rejects missing or non-string interval fields through its CLI. Interval records
point to the UCI source entry.

The decision ledger now gives every candidate an artifact-identity state and an
outcome definition. C-MAPSS manifests include observed counts and describe its
license status accurately. The quickstart records results from the downloaded
artifacts, including the FD004 readme discrepancy. No public dataset files are
stored in the repository.

The four examples use separate parsers and reports because their schemas,
outcomes, and evidence differ. Dataset outcomes remain non-poolable;
MetroPT-3 observations outside reported intervals remain censored. The shared
README and Feature 039 specification now frame these as one evidence-bounded
example set while preserving Feature 038 as the AI4I implementation history.

## Architecture review (2026-09-22)

Each dataset keeps its own parser, expectations, and report because the source
schemas and outcome evidence differ. Shared code stays limited to the common
chunked SHA-256 and stable error-deduplication helpers; the AI4I verifier uses
both shared helpers. The MetroPT-3 CLI validates interval manifest fields
before constructing domain values and preserves the standard failure-report
envelope. No generic verified-dataset type or automatic adapter into public
corpus admission was added: structural verification alone does not provide
split, horizon, lineage, or admission evidence. Outcome definitions continue to
meet at the existing `OutcomeDefinition`/commensurability interface.

Final verification (2026-09-22): focused dataset/AI4I tests pass (36 tests);
the full suite passes (475 passed, 1 skipped) with 98.01% aggregate
branch-aware coverage, and every production module meets the 95% branch-aware
floor. Ruff lint and formatting, all pre-commit hooks, the synthetic demo, and
the dependency audit pass. `pip-audit` reports no known vulnerabilities; it
skips the local `isoprax-reference` package because it is not published on
PyPI. The final diff passes whitespace/error checks.

## Multi-example documentation alignment (2026-09-22)

Feature 039 is now the shared evidence-bounded overview for AI4I, ApacheJIT,
C-MAPSS, and MetroPT-3; Feature 038 remains the detailed AI4I implementation
record. The root README and AI4I example notes link readers to the complete
set and distinguish each example's evidence role. Repository-relative link
targets and quickstart anchors were checked, `git diff --check` passed, and the
documentation whitespace scan found no trailing whitespace. This update was
documentation-only, so source tests were not rerun; the code verification
results above predate this documentation reframe.

## Code-review follow-ups (2026-09-22)

The focused review follow-ups close the remaining acceptance gaps. MetroPT-3
now advances its time baseline for each valid observation, reports cadence and
monotonicity from adjacent valid rows, counts interval coverage for every valid
row (including the first valid row after malformed input), rejects
whitespace-padded/duplicate anchor identities, and counts each accepted anchor
identity once. ApacheJIT JSON reports per-project positive yield as buggy rows
divided by project rows, including an explicit zero for projects with no buggy
rows. Passing-path fixtures now cover C-MAPSS train/test/RUL alignment and
MetroPT-3 anchored coverage. The AI4I CLI returns a deterministic unavailable
snapshot report when no local path is supplied and does not fetch data.

Verification: `make coverage` passed with 481 tests passed, 1 skipped, 98.00%
aggregate branch-aware coverage, and every production module at or above the
95% branch-aware floor. Focused AI4I/public-dataset tests passed (42 tests), and
Ruff lint and formatting checks passed. These are structural verifier and CLI
checks only; they do not establish predictive efficacy or production validation.

## Fact-based MetroPT-3 time contract (2026-09-22)

The UCI record lists the timestamp as a date/time and publishes the four failure
intervals without timezone information. The verifier therefore compares those
date/time values as written; it neither assigns UTC nor converts offsets. The
interval manifest was changed to omit `Z`, and both the CLI/API interval seam
and CSV parser reject timezone-qualified values until an authoritative timezone
mapping is available. This preserves the observed interval-coverage semantics
without making an unsupported absolute-time claim.

Verification for this correction: `make coverage` passed with 483 tests passed,
1 skipped, 98.00% aggregate branch-aware coverage, and every production module
at or above the 95% floor. Ruff lint/format, `uv lock --check`, `git diff --check`,
and the scoped pre-commit hooks also passed.
