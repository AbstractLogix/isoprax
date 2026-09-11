# Feature Specification: Unified Commensurability Policy

**Feature Branch**: `022-commensurability-policy`

## Summary

Ensure all public commensurability callers use the same attestation and
retained-observation policy rather than silently applying different pooling
rules.

## Acceptance scenarios

1. `require_commensurable` accepts explicit attestation and retained-
   observation evidence and rejects the same inputs when omitted.
2. `cross_family_report` receives the same policy inputs and bases pooled
   metric emission on `pooling_allowed`, not only direct `commensurable` status.
3. Bridgeable definitions remain visibly labeled as bridgeable; pooling does
   not become a Semantic or Full Conformance claim.

## Claim boundary

This aligns policy plumbing. It does not create an attestation or imply that
retained observations exist when the caller has not supplied that evidence.
