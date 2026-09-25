# Research: Haskell Reference Semantics Kernel

## Toolchain

**Decision**: Pin GHC 9.14.1 and Cabal 3.16.1.0, and freeze all package resolutions in the kernel directory.

**Rationale**: GHC 9.14.1 is a stable release supported by the official GHC downloads and its documentation requires Cabal 3.16 or later. A newer release candidate is not needed for this isolated reference kernel.

**Alternatives considered**: Debian's older GHC package was available but was not selected because it would create a less representative baseline. An unpinned latest compiler was rejected because it would make independent semantic evidence harder to reproduce.

## JSON, canonicalization, and identity

**Decision**: Parse into Aeson JSON values, reject duplicate keys at the parser boundary, and use a pinned RFC 8785 encoder only if it passes the shared Python and RFC vectors. Hash the exact returned UTF-8 bytes with SHA-256.

**Rationale**: RFC 8785 defines invariant canonical JSON for hashing and signing, including deterministic property sorting, I-JSON constraints, and ECMAScript-compatible number serialization. The Python implementation already uses rfc8785.dumps; the Haskell kernel must compare bytes before comparing hashes.

**Alternatives considered**: Aeson ordinary encoding is not canonical. Direct use of its RFC 8785 encoder without regression vectors was rejected because its documentation calls out a binary64 conversion example (1e23) that can differ from ECMAScript formatting. The frozen implementation must pass 1e23, safe-integer boundaries, negative zero, exponent notation, Unicode escaping, and RFC vectors before it can be treated as normative.

**Release gate**: If the encoder fails any shared I-JSON vector, repair the Haskell serializer or select a compatible implementation; never silently narrow the supported numeric domain after tests are written.

## Semantic model and differential reference

**Decision**: Build opaque validated values and pure evaluators for outcome definitions, attestations, explicit bridge records, calibration, the selected admission gates, and Stage 0 conformance projection. The Python adapter calls check_commensurable, check_calibration_conformance, cross_family_report, and the corresponding existing private admission gate functions.

**Rationale**: This yields independent Haskell decisions while tying fixtures to actual repository behavior. Stage 0 must stay Structural; commensurability and calibration are necessary evidence, but they do not upgrade the current Isoprax Stage 0 implementation to Semantic or Full.

**Bridge-policy reconciliation**: Feature 014 classifies window/threshold mismatch as bridgeable. Feature 022 preserves the current policy that retained observations can authorize a labeled bridgeable pooling path. The kernel requires a complete, endpoint-bound bridge descriptor and the Python test adapter maps a valid descriptor to the existing retained-observation boolean. This is stricter wire validation, not a changed decision for equivalent supported evidence. The kernel does not inspect retained rows or verify a transform.

**Selected admission scope**: Reuse only calibration-fit/gate split separation and provenance/predeclaration eligibility. Do not port the other nine Stage 1 admission gates.

## Type-safety experiment

**Decision**: Expose abstract PoolingEvidence and CalibratedEvidence values. Their constructors are private. Only successful smart constructors can produce them, and authorizePooledComparison requires all three evidence values.

**Rationale**: This uses ordinary sum/product types and module abstraction, without type-level identifiers, template metaprogramming, or a Haskell rewrite. Compile-fail examples make the claimed benefit executable.

**Alternatives considered**: Phantom-type IDs would not be soundly derivable from dynamic CLI JSON without substantially expanding the design; they were rejected as disproportionate for this experiment.

## Property and differential strategy

Properties cover normalized equality, symmetry for valid supported pairs, direct reflexivity, sorted threshold semantics, fail-closed incompatible event/process mismatches, bridge/attestation endpoint binding, calibration boundary rules, fit/gate disjointness, provenance timing, and stable canonical identity. Every property runs at least 1,000 cases with QuickCheck replay seeds available on failure.

Differential fixtures store request JSON and expected normalized result. The Python harness builds the same typed Python records, calls existing Isoprax functions, and compares outcome level, commensurable, pooling_allowed, sorted differing fields, calibration pass flags, selected gate pass flags, Stage 0 claim label, canonical bytes, and SHA-256. Human-readable Python reason text is mapped to stable reason categories only; no semantic decisions are normalized away.

## Benchmark method

Measure first CLI invocation and at least 100 subsequent subprocess invocations after building the executable. Compare the equivalent Python in-process commensurability and identity operations. Report p50/p95, sample count, OS/CPU, GHC/Cabal/Python versions, and separate the process-startup overhead. No performance claim is a keep criterion by itself.

## References

- [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785)
- [GHC 9.14.1 official download and compatibility notes](https://ghc.gitlab.haskell.org/homepage/download_ghc_9_14_1.html)
- [Aeson RFC 8785 API](https://hackage-content-origin.haskell.org/package/aeson-2.3.0.0/docs/Data-Aeson-RFC8785.html)
