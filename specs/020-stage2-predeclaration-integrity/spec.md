# Feature Specification: Stage 2 Predeclaration Integrity

**Feature Branch**: `020-stage2-predeclaration-integrity`

## Summary

Make the released `traefik/whoami` Stage 2 pilot path verify the
predeclaration artifact it reads, use its declared outcome semantics, and call
the existing provenance verifier before producing a feasibility report.

## Acceptance scenarios

1. Editing any hashed predeclaration field causes the pilot command to fail
   before report generation.
2. The declared predeclaration commit must be the commit that introduced the
   artifact and must be an ancestor of the corpus-data commit.
3. The pilot profile derives observation process, window, thresholds, and
   family descriptions from the predeclaration rather than script constants.
4. A valid committed artifact still produces the existing feasibility report.

## Claim boundary

This closes a provenance/evidence integrity gap. It does not turn the pilot
into a Semantic or Full Conformance result.
