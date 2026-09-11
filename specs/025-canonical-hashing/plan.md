# Implementation Plan: Shared Canonical Evidence Identities

Add `isoprax.identity` with `canonical_json`, `content_hash`, and `bytes_hash`.
Replace the duplicated `_canonical`/`_hash` pairs in the evidence reducers and
the replay predeclaration hash helper, preserving public APIs and report
payloads. Add stable utility tests and run the complete suite.
