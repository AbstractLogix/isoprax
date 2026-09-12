# Convergence: Stage 2 Corpus Evaluation Gate

This file records the final spec-to-code review for Feature 018.

## Initial state

The repository has Stage 2 replay-feasibility evidence and Stage 1 per-family
evaluation, but no corpus-level gate combining provenance, split integrity,
label yield, non-degenerate prediction, and family-scoped evaluation.

## Decision 001: evidence-scale corpus defaults

The original defaults of four test rows and two observations of each outcome
class were structural smoke-test values, not defensible evaluation defaults.
They are replaced by 800 labeled test rows per family, with at least 50
positive and 50 negative outcomes and maximum ECE `0.05`. Existing tests retain
small values only through explicit profile overrides, making their plumbing
scope visible.

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
