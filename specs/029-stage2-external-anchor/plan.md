# Implementation Plan

1. Add the Sigstore dependency and a small verifier for offline DSSE bundles.
2. Validate the in-toto statement's type, subject digest, predicate digest, and
   predeclaration commit before marking the anchor verified.
3. Thread optional bundle and signer arguments through the whoami pilot while
   retaining an explicit inconclusive result when no bundle is supplied.
4. Add an attestation-generation script and regression tests for missing,
   malformed, and mismatched evidence.
