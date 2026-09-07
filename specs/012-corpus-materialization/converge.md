# Feature 012 Convergence

**Date**: 2026-09-07

## Implemented

- Added deterministic public corpus snapshot normalization with RFC3339 UTC
  validation, canonical identities, stable ordering, and preserved outcome and
  lineage fields.
- Added `PublicCorpusMaterializationProfile`, `PublicCorpusReport`, and
  `WithheldEvidenceRecord` so one frozen profile produces an inspectable local
  manifest with explicit rejection inventory.
- Added fail-closed handling for private, privileged, malformed, duplicate,
  and profile-mismatched evidence without network access or label substitution.
- Added deterministic tests for permutations, censoring, preservation,
  rejection paths, profile mismatches, and report identity.

## Verification obtained

- `uv run pytest tests/test_public_corpus.py -q --no-cov`: **19 passed**.
- `uv run pytest tests -q --cov-report=xml`: **208 passed**, **97.24%** total.
- `uv run python scripts/check_module_coverage.py coverage.json --minimum 95`:
  passed; every production module meets the threshold.
- Ruff check, format check, and `git diff --check`: passed.

## Claim boundary

The materialized report is a deterministic public-corpus evidence artifact
only. It does not acquire data, recompute outcomes, grant admission, or imply
Semantic/Full Conformance.
