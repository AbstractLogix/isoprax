# Feature Specification: Stage 2 Predeclaration Integrity

**Feature Branch**: `020-stage2-predeclaration-integrity`

## Summary

Make the released `traefik/whoami` Stage 2 pilot path verify the
predeclaration artifact it reads, use its declared outcome semantics, and call
the existing provenance verifier before producing a feasibility report. Until
an external anchor is independently verified, the pilot must emit an explicit
`inconclusive` result and no feasibility report.

## Acceptance scenarios

1. Editing any hashed predeclaration field causes the pilot command to fail
   before report generation.
2. The declared predeclaration commit must be the commit that introduced the
   artifact and must be an ancestor of the corpus-data commit.
3. The pilot profile derives observation process, window, thresholds, and
   family descriptions from the predeclaration rather than script constants.
4. A valid artifact with an unverified external anchor produces a machine-
   readable `inconclusive` result without a feasibility report.
5. A valid artifact with an independently verified external anchor may
   proceed to the existing feasibility report path.

## Claim boundary

This closes a provenance/evidence integrity gap. A repository URL is not
treated as an independent anchor. The pilot does not turn into a Semantic or
Full Conformance result, and remains inconclusive until third-party anchor
verification is implemented and supplied.
