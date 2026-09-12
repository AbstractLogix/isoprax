# Feature Specification: RFC 8785 Evidence Identity

**Feature Branch**: `031-rfc8785-evidence-identity`

## Summary

Replace Python-specific JSON serialization in evidence identities with RFC
8785 JSON Canonicalization Scheme (JCS), so a report or predeclaration hash
can be independently recomputed by another language implementation.

## Acceptance scenarios

1. Mapping order, Unicode, and numerically equivalent JSON values produce the
   RFC 8785 representation.
2. Unsupported values, NaN/infinite floats, and integers outside the JCS safe
   integer domain are rejected rather than stringified into a different value.
3. Existing identity consumers use the shared JCS helper and retain stable
   hashes for values already representable under JCS.

## Claim boundary

This makes artifact identity serialization cross-language specified. A matching
hash proves content identity only; it does not prove provenance, authorship,
or external timestamp ordering.
