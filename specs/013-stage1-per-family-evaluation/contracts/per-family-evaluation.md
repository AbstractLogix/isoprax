# Library Contract: Per-Family Stage 1 Evaluation

## Inputs

### `PerFamilyEvaluationProfile`

Defines frozen, predeclared evaluation constraints for one family.

### `evaluate_per_family(...)`

```text
evaluate_per_family(
  rows: Iterable[CorpusRow],
  admission_profile: AdmissionProfile,
  admission_report: AdmissionReport,
  profile: PerFamilyEvaluationProfile,
) -> PerFamilyEvaluationReport
```

## Behavioral guarantees

1. Equivalent valid inputs MUST yield byte-stable canonical identity and
   equivalent report payloads.
2. Evaluation MUST fail closed on:
   - non-admitted corpus evidence,
   - post-hoc threshold/version mismatch,
   - missing predeclaration,
   - invalid or missing score fields,
   - non-isolated calibration split evidence.
3. Missing required evidence MUST be represented explicitly as
   `unavailable_evidence` and produce `inconclusive` status where applicable.
4. Claim boundary MUST explicitly prohibit Semantic/Full promotion,
   cross-family pooling, and efficacy claims beyond scoped evidence.

## Outputs

### `PerFamilyEvaluationReport`

- deterministic `evaluation_identity`
- status (`evaluation_evidence`, `blocked`, `inconclusive`)
- predeclared metrics subset
- calibration qualifier and diagnostics
- counts/uncertainty summaries
- immutable claim boundary
