# Feature Specification: Stage 2 External Anchor Verification

**Feature Branch**: `029-stage2-external-anchor`

## Summary

Make the Stage 2 pilot verify a real independent anchor before emitting replay
feasibility evidence. The accepted anchor is a Sigstore DSSE bundle containing
an in-toto Statement whose subject and predicate bind the exact
predeclaration hash and introducing commit. Sigstore/Rekor verification is
performed offline from the supplied bundle.

## Acceptance scenarios

1. A missing, malformed, unsigned, incorrectly signed, or incorrectly bound
   bundle produces `external_anchor_status: "unverified"` and no
   `feasibility_report`.
2. A valid Sigstore bundle with a valid Rekor inclusion proof and matching
   in-toto subject/predicate permits the existing feasibility reducer to run.
3. The pilot exposes a command that builds the canonical in-toto Statement
   with Sigstore's Python API and signs it through `Signer.sign_dsse`, allowing
   Rekor to provide the independent timestamp and transparency-log evidence.

## Claim boundary

This verifies ordering evidence for the bounded replay-feasibility pilot. It
does not establish model efficacy, Semantic Conformance, Full Conformance, or
the availability of an attestation for the checked-in historical pilot.
