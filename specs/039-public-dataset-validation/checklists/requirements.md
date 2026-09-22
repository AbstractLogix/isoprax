# Requirements Checklist: Evidence-Bounded Dataset Examples

## Scope and provenance

- [x] AI4I 2020 is included as the synthetic structural/label-semantics baseline and links to its detailed Feature 038 record.
- [x] ApacheJIT is admitted from a canonical Zenodo identity, with Kaggle retained as discovery/mirror metadata.
- [x] C-MAPSS is explicitly classified as simulated run-to-failure/RUL evidence.
- [x] MetroPT-3 is explicitly classified as external-anchor-dependent single-stream evidence.
- [x] Deferred, fixture-only, rejected, and unavailable candidates remain visible in the decision ledger.
- [x] No public artifact is vendored and no verifier downloads data.

## Structural and temporal verification

- [x] AI4I schema, snapshot identity, composite/mode counts, and label discrepancies are verified without leakage or source repair.
- [x] ApacheJIT schema, row count, commit uniqueness, labels, finite metrics, project distribution, hash, inversion, and year/epoch diagnostics are checked.
- [x] C-MAPSS 26-field rows, finite numeric values, unit/cycle continuity, train/test counts, RUL alignment, and hashes are checked.
- [x] MetroPT-3 schema, row and timestamp identity, monotonicity, finite signals, observed cadence, explicit anchors, and interval coverage are checked.
- [x] Failures identify named invariants and do not repair, drop, relabel, or infer negatives.

## Isoprax claim boundaries

- [x] The root README presents all four examples, their different evidence roles, provenance, and run instructions.
- [x] Outcome definitions are distinct and use existing Isoprax types.
- [x] Focused tests prove event/observation-process mismatches are irreducible and non-poolable.
- [x] Reports and documentation state that verification is not efficacy, production validation, Semantic Conformance, or Full Conformance.
