# Feature 014 Convergence

**Date**: 2026-09-07

## Implemented evidence

- Vendored the exact user-established Isoprax v0.3 POC source at
  `docs/isoprax-v0.3-poc.md`; provenance is recorded beside it.
- Added a derived citation index for Section 8's ordered obligations so
  references such as 8.2 resolve to stable repository anchors without changing
  the authoritative source text.
- Added machine resolution for implementation and example citations,
  including numbered sections and Appendix D.3. Unresolved citations fail the
  focused test.
- Replaced prose-only Outcome Definition comparison with structured window,
  threshold, observation-process, and attestation values. Comparisons now
  classify direct, attested, bridgeable, and irreducible cases.
- Added a deterministic seven-day versus ninety-day pooling-harm fixture:
  each family ECE is 0.000, pooled ECE is 0.000, per-family top-k precision is
  1.000, pooled precision is 0.500, and degradation is 0.500.
- Added discrimination diagnostics and prevented constant base-rate predictors
  from receiving a qualified calibrated declaration.
- Added `HistoricalMeanForecastStrategy` and verified score-free
  `ForecastSignal` SQLiteKB round-trip behavior.
- Added a provenance/license-aware public label evidence reducer. The checked-in
  manifest is explicitly blocked because no public snapshot is bundled.

## Verification obtained

- `uv run pytest tests -q`: **204 passed**.
- Coverage: **97.30%**, above the repository 95% threshold.
- `uv run ruff check isoprax tests examples`: passed.
- `uv run ruff format --check isoprax tests examples`: passed.
- `uv run python examples/demo_cross_family.py`: completed; retained
  Structural-only claim boundary.
- `git diff --check`: run as final handoff check.

## Remaining boundary

The public SZZ-style lane has a manifest and fail-closed reducer but no bundled
licensed source snapshot. Its current status is blocked/inconclusive evidence,
not a real-world validation result and not Semantic/Full Conformance.
