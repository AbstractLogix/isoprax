# Implementation Plan

1. Add the Sigstore dependency and a small verifier for offline DSSE bundles.
2. Define the canonical in-toto Statement once, then use it for both signing
   and verification. Validate its type, subject digest, predicate digest, and
   predeclaration commit before marking the anchor verified.
3. Thread optional bundle and signer arguments through the whoami pilot while
   retaining an explicit inconclusive result when no bundle is supplied.
4. Add an attestation-generation script using Sigstore's Python signing API,
   plus a real production bundle fixture and regression tests for missing,
   malformed, mismatched, and externally valid bundle evidence.
