# Data Model: Stage 1 Per-Family Evaluation

## PerFamilyEvaluationProfile

Frozen configuration for one family evaluation run.

| Field | Rule |
| --- | --- |
| `family` | Non-empty family identifier (single-family scope). |
| `outcome_definition` | Required `OutcomeDefinition` used for interpretability and claim boundaries. |
| `score_field` | Required predeclared prediction field in admitted rows. |
| `predeclared_threshold_version` | Required; each row must match exactly. |
| `predeclared_metrics` | Non-empty unique subset of canonical metric names. |

## UnavailableEvaluationEvidence

Represents one missing/incomplete evidence category.

| Field | Rule |
| --- | --- |
| `category` | Canonical category name (e.g., `calibration_gate_rows`). |
| `reason` | Human-readable bounded reason. |

## PerFamilyEvaluationReport

Deterministic evaluation output for one family.

| Field | Rule |
| --- | --- |
| `evaluation_identity` | Canonical SHA-256 over public report payload. |
| `status` | `evaluation_evidence`, `blocked`, or `inconclusive`. |
| `family` | Copied from evaluation profile. |
| `outcome_definition_id` | From profile outcome definition. |
| `declarable_class` | Evidence-only declarable text, never Semantic/Full. |
| `metrics` | Predeclared metric results when evaluable. |
| `calibration` | Calibration qualifier and diagnostics from gate rows. |
| `counts` | Row/test/censored counts for reproducibility. |
| `uncertainty` | Confidence interval summary for reported positive rate. |
| `unavailable_evidence` | Ordered explicit missing evidence entries. |
| `claim_boundary` | Immutable non-pooling, non-escalation boundary statement. |

## State transitions

1. **Input Validation**: Validate profile, admission pass state, split evidence,
   threshold version, and score field constraints.
2. **Reduction**: Extract split-specific observed outcomes and scores.
3. **Evaluation**: Compute predeclared metrics/calibration/uncertainty if
   sufficient evidence exists.
4. **Status Resolution**:
   - `blocked`: admission did not pass.
   - `inconclusive`: required evidence missing.
   - `evaluation_evidence`: complete per-family evidentiary output.
