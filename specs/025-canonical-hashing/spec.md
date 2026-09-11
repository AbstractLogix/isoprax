# Feature Specification: Shared Canonical Evidence Identities

**Feature Branch**: `025-canonical-hashing`

## Summary

Provide one shared canonical serializer and content-hash implementation for
evidence identities, replacing duplicated module-local implementations that
already differ in their JSON fallback behavior.

## Acceptance scenarios

1. All report/profile/corpus identity reducers use the shared content hash.
2. Canonical serialization is key-sorted, compact, UTF-8 encoded, and handles
   the existing non-JSON fallback consistently.
3. Existing identity outputs remain stable for current payloads.
4. Byte-level artifact hashes use the same shared SHA-256 primitive.

## Claim boundary

This removes identity implementation drift. It does not validate the truth of
the payloads being hashed or expand any evidence claim.
