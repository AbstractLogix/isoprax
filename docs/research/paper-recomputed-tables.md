# Recomputed manuscript tables

Generated from the deterministic Benchmark A source and frozen operation-gate case records. The gate counts are independently reduced from the 23 case rows.

## Table 1. Synthetic forecast targets and declared mixtures [[C9]]

| Condition | Exact target ID | n | Mean forecast | Event rate | Brier | ROC AUC | Evidence |
|---|---|---:|---:|---:|---:|---|---|
| change | `synthetic.change.fix-linked-defect.30d` | 100 | 0.800 | 0.800 | 0.160 | not available (constant scores) | [[C9]] |
| operational | `synthetic.operations.threshold-breach.30m` | 100 | 0.800 | 0.800 | 0.160 | not available (constant scores) | [[C9]] |
| control-a (positive control) | `synthetic.shared.threshold-breach.30m` | 100 | 0.800 | 0.800 | 0.160 | not available (constant scores) | [[C9]] |
| control-b (positive control) | `synthetic.shared.threshold-breach.30m` | 100 | 0.800 | 0.800 | 0.160 | not available (constant scores) | [[C9]] |
| Different-target numeric mixture | `synthetic.mixture.change-30d-and-operational-30m.equal-weight` | 200 | 0.800 | 0.800 | 0.160 | not available (constant scores) | [[C9]] |
| Same-target positive-control mixture | `synthetic.shared.threshold-breach.30m` | 200 | 0.800 | 0.800 | 0.160 | not available (constant scores) | [[C9]] |

The different-target row is the named 50:50 mixture in the table; it is not a forecast of one common event.

## Table 2. Operation-specific rule challenge [[C10]]

The challenge cases are internally authored. Counts are descriptive and are not population error rates.

| Rule | False permissions / invalid cases | Unnecessary refusals / valid cases | Interpretation errors / cases | Evidence |
|---|---:|---:|---:|---|
| global label | 7/12 | 3/11 | 3/23 | [[C10]] |
| metadata only | 5/12 | 0/11 | 0/23 | [[C10]] |
| naive aggregation | 12/12 | 0/11 | 8/23 | [[C10]] |
| operation specific | 0/12 | 0/11 | 0/23 | [[C10]] |
