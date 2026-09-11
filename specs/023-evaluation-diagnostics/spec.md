# Feature Specification: Evaluation Diagnostic Input Integrity

**Feature Branch**: `023-evaluation-diagnostics`

## Summary

Make evaluation primitives reject invalid, empty, or ambiguous inputs with
domain errors instead of NaNs, NumPy internals, or silently empty splits.
Remove the unused `all_strategy_types` report parameter.

## Acceptance scenarios

1. Brier, reliability, and ECE diagnostics reject mismatched input lengths and
   invalid score/outcome values.
2. Brier and paired-comparison diagnostics reject empty inputs.
3. Reliability bins require a positive integer count.
4. Time-sliced evaluation rejects train fractions outside `(0, 1)`.
5. Cross-family reporting has no ignored strategy-type parameter.

## Claim boundary

This hardens diagnostic input handling. It does not alter the conformance
claim boundary or create performance evidence.
