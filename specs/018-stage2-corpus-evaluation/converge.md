# Convergence: Stage 2 Corpus Evaluation Gate

This file records the final spec-to-code review for Feature 018.

## Initial state

The repository has Stage 2 replay-feasibility evidence and Stage 1 per-family
evaluation, but no corpus-level gate combining provenance, split integrity,
label yield, non-degenerate prediction, and family-scoped evaluation.

## Closure criteria

- [ ] Profile and report contracts implemented.
- [ ] All rejection paths have focused tests.
- [ ] Constant-score predictors cannot qualify.
- [ ] No pooled or Semantic claim is emitted.
- [ ] Full repository gates pass.
