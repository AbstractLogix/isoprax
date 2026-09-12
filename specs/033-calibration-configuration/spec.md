# Feature Specification: Configurable Cross-Family Calibration

**Feature Branch**: `033-calibration-configuration`

## Summary

Expose the calibration-conformance parameters on `cross_family_report` so a
caller can select the minimum event count, bin count, and maximum ECE instead
of receiving a result produced by hidden defaults.

## Acceptance scenarios

1. The cross-family path accepts `min_events`, `n_bins`, and `max_ece`.
2. The selected configuration controls both family checks and pooled ECE.
3. The report renders and retains the selected values for auditability.

## Claim boundary

This makes diagnostic configuration visible. It does not make a result
calibrated or establish cross-family commensurability.
