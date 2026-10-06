# Contract: Synthetic Experiment Result

The runner MUST:

1. Emit valid JSON with a stable key order and deterministic numeric values for fixed code, Python dependencies, and seed.
2. Identify every run as synthetic and state the claim boundary.
3. Preserve target identity in all per-target results.
4. Include the exact estimand and weights before every pooled metric.
5. Omit pooled metrics for different-family and different-horizon cases.
6. Include event counts and uncertainty method for each shared-model target.
7. Mark ROC AUC unavailable when the sample does not contain both outcomes.
8. Report all four policy rules and their false permissions, unnecessary refusals, interpretation errors, ranking changes, and decision changes.
9. Include operation permissions as research findings only; do not wire them into IsoPrax runtime admission or enforcement.

The report MUST state that the gate challenge set is synthetic and authored from the candidate rules. Its counts are not field error rates.
