# Python Semantic Types

Python remains the only maintained implementation of Isoprax semantic decisions. Corpus construction, numerical evaluation, ML/JEPA, experimentation, visualization, notebooks, and orchestration also remain Python-owned.

## What the types protect

- `OutcomeDefinition` accepts the supported string and mapping input forms, validates nested structures, and stores normalized `ObservationProcess`, `Window`, and immutable threshold tuple values.
- `ObservationProcess`, `Window`, and `Threshold` enforce their field invariants on direct construction as well as at their raw mapping boundaries.
- Commensurability returns a closed union of direct, bridgeable, and irreducible result types. Attestations are retained as provenance only; neither attestation nor retained observations authorizes pooling before outcomes are re-derived under a shared definition.
- Generic marker types carry left/right outcome-family identity across calibration and commensurability evidence. Evidence factories check concrete definition IDs and direction at runtime.
- `authorized_pooled_ece` requires the authorization token and exact score/outcome samples whose canonical digests were checked during calibration. Calibration labels must be exact binary integers; no truncating conversion occurs. A type checker rejects omitted, wrong-family, and reversed evidence in the supplied negative examples.
- Admission splits, row outcome classes, gate IDs, calibration declarations, and commensurability levels use finite types in the checked semantic scope.
- Cross-family reports remain Structural at Stage 0 regardless of calibration or pooling evidence.

The high-level `cross_family_report` facade computes per-side calibration diagnostics from the same arrays it reports. It can display pooled ECE for directly commensurable definitions as a calibration diagnostic, marks failed calibration as uncalibrated, and withholds pooled ECE for non-commensurable definitions.

Run `uv run mypy` for the strict semantic file set. The checker covers `isoprax/commensurability.py`, `isoprax/semantic_types.py`, `isoprax/evaluation.py`, and `isoprax/admission.py`. The configured exception is limited to missing third-party typing metadata for SciPy and scikit-learn imports; the checked modules' own definitions remain strict.

## Limits

Python's static types cannot prove that JSON/database values share the same definition ID. A marker class is a code-level declaration used to statically align evidence types; runtime factories still compare the actual IDs. Sample digests prevent swapping arrays after calibration but do not independently prove external sample provenance. Callers can deliberately bypass static checks with `Any`, casts, untyped code, or private module internals, so the API also validates evidence at runtime.

The completed Haskell implementation and its cross-runtime report were a useful experiment, but maintaining a second specification implementation is no longer part of the architecture. Its assessment and verification results remain in [the archived experiment record](../specs/042-haskell-semantics-kernel/assessment.md).

## Assessment

This is a correctness improvement, not only an annotation pass. The strict checker exposes normalized stored fields and finite decision states, and typed authorization makes required evidence explicit in its signature. Review also found and fixed three Python issues: a pooled-evaluation token could be reused with unrelated arrays; retained observations alone authorized aggregation of still non-commensurable definitions; and empty required definition fields could compare equal. The mixed-threshold property additionally exposed a sorting `TypeError` for matching metric/operator pairs with a numeric value on one side and text on the other. Regression and property tests cover each correction. Earlier Haskell differential fixes were confined to the experimental Haskell implementation and did not establish that Python was bug-free.
