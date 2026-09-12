# Feature Specification: Versioned Signal Identity

**Feature Branch**: `030-versioned-signal-identity`

## Summary

Make `strategy_version` part of a persisted signal's identity. Multiple
versions of one strategy may score the same event, but a signal version remains
immutable once stored and all outcome/calibration links identify the version
they describe.

## Acceptance scenarios

1. `(event_id, strategy_id, strategy_version)` is unique and an exact retry is
   idempotent.
2. Two versions coexist and are retrievable only by explicit version when the
   lookup would otherwise be ambiguous.
3. An outcome with multiple candidate signal versions must name its version;
   labeled-pair queries likewise refuse to mix versions implicitly.
4. Existing databases migrate to the versioned key; rows with missing or
   ambiguous version linkage fail closed.

## Claim boundary

This fixes persistence identity and linkage. It does not assert that any
strategy version is better, calibrated, or semantically comparable.
