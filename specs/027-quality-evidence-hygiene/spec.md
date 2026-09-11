# Feature Specification: Quality and Release Evidence Hygiene

**Feature Branch**: `027-quality-evidence-hygiene`

## Summary

Close the review's repository-quality gaps by establishing changelog/version
consistency, ignoring local Hypothesis state, broadening mutation configuration
to the production package, and adding property coverage for predeclaration
identity serialization.

## Acceptance scenarios

1. The package version has a matching changelog release heading.
2. `.hypothesis/` is ignored as local test state.
3. Mutation configuration no longer restricts evidence to one production
   module and runs the full test corpus.
4. Predeclaration identity hashing is property-tested across mapping insertion
   orders.

## Claim boundary

These are release and testing controls. Mutation/property results do not prove
external platform, device, production, or conformance claims.
