# Feature Specification: Admission Timestamp Integrity

**Feature Branch**: `021-admission-time-integrity`

## Summary

Make Stage 1 admission timestamp parsing use one strict RFC 3339 UTC contract
and ensure malformed row timestamps fail the relevant admission gate instead of
raising an aware/naive datetime exception.

## Acceptance scenarios

1. Naive or non-UTC split boundaries are rejected at construction time.
2. Naive, malformed, or non-UTC row score timestamps produce a failed
   `split_followup` gate and do not crash `evaluate_admission`.
3. Existing `Z` and explicit UTC-offset timestamps remain accepted.

## Claim boundary

This hardens admission input validation only; it does not establish corpus
quality or any conformance class.
