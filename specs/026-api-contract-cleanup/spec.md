# Feature Specification: API Contract Cleanup

**Feature Branch**: `026-api-contract-cleanup`

## Summary

Make abstract KB retrieval capabilities genuinely abstract, expose one
canonical name for each predeclaration operation, and report adequacy failures
with row identifiers rather than split names.

## Acceptance scenarios

1. A partial `KnowledgeBase` implementation cannot be instantiated without
   `get_event` and `get_signal`.
2. The package exports canonical predeclaration operation names without
   duplicate validate/check aliases.
3. An adequacy failure reports the IDs of rows in deficient splits.

## Claim boundary

This clarifies API contracts and diagnostics. It does not change evidence
eligibility or conformance claims.
