# Feature Specification: Strict RFC 3339 UTC Timestamps

**Feature Branch**: `028-strict-rfc3339`

## Summary

Make Stage 1 admission accept only timestamps that are explicitly RFC 3339
UTC values, including the required `T` separator.

## Acceptance scenarios

1. Valid `Z` and `+00:00` timestamps remain accepted.
2. Naive, non-UTC, malformed, and space-separated timestamps are rejected.
3. Existing admission behavior and domain error messages remain unchanged for
   other inputs.

## Claim boundary

This tightens timestamp parsing. It does not establish external chronology or
prove any Semantic or Full Conformance claim.
