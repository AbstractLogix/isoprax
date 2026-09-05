# Library Contract: Stage 1 Admission Layer

The Stage 1 admission layer extends the existing Isoprax contract surface with
admission-specific validation and reporting behavior.

## Contract obligations

- Admission input MUST include immutable lineage identifiers from change to
  deployment to observation.
- Admission MUST reject prediction-time leakage fields and report exact
  offending fields.
- Admission MUST classify rows as observed-positive, observed-negative, or
  censored; censored rows MUST NOT be counted as negatives.
- Admission MUST enforce frozen chronological split boundaries and disallow
  post-hoc boundary edits.
- Admission output MUST include deterministic gate-by-gate evidence and MUST
  NOT assign Semantic or Full conformance status.

## Compatibility constraints

- Existing Stage 0 event/signal/outcome semantics remain normative.
- Admission is an evidence gate only; conformance class decisions remain a
  separate evidence-review layer.
