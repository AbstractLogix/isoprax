# Convergence: Stage 2 Corpus Evaluation Gate

This file records the final spec-to-code review for Feature 018.

## Initial state

The repository has Stage 2 replay-feasibility evidence and Stage 1 per-family
evaluation, but no corpus-level gate combining provenance, split integrity,
label yield, non-degenerate prediction, and family-scoped evaluation.

## Closure criteria

- [X] Profile and report contracts implemented.
- [X] All rejection paths have focused tests.
- [X] Constant-score predictors cannot qualify.
- [X] No pooled or Semantic claim is emitted.
- [X] Full repository gates pass.

## Evidence

The reducer is implemented in `isoprax/stage2_corpus_evaluation.py` and
covered by `tests/test_stage2_corpus_evaluation.py`. The real whoami feasibility
pilot remains an input evidence package; its all-negative result is correctly
inconclusive for this qualified corpus-evaluation gate.
