# Python Semantic Types

Python remains the only runtime implementation of Isoprax semantic decisions. Corpus construction, numerical evaluation, ML/JEPA, experimentation, visualization, notebooks, and orchestration also remain Python-owned. A compact Haskell implementation checks the semantic proof boundary in CI only; no Python runtime path calls it.

## What the types protect

- `OutcomeDefinition` accepts the supported string and mapping input forms, validates nested structures, and stores normalized `ObservationProcess`, `Window`, and immutable threshold tuple values.
- `ObservationProcess`, `Window`, and `Threshold` enforce their field invariants on direct construction as well as at their raw mapping boundaries.
- Commensurability returns a closed union of direct, bridgeable, and irreducible result types. Attestations are retained as provenance only; neither attestation nor retained observations authorizes pooling before outcomes are re-derived under a shared definition.
- Generic marker types carry left/right outcome-family identity across calibration and commensurability evidence. Evidence factories check concrete definition IDs, normalized semantic-content digests, and direction at runtime.
- `authorized_pooled_ece` requires the authorization token and exact score/outcome samples whose canonical digests were checked during calibration. The token also binds one `CalibrationPolicy` containing `min_events`, `n_bins`, and `max_ece`; pooled ECE uses its bin count. Calibration labels must be exact binary integers; no truncating conversion occurs. A type checker rejects omitted, wrong-family, and reversed evidence in the supplied negative examples.
- Admission splits, row outcome classes, gate IDs, calibration declarations, and commensurability levels use finite types in the checked semantic scope.
- Cross-family reports remain Structural at Stage 0 regardless of calibration or pooling evidence.

`cross_family_report` is a diagnostic facade, not an authorization path. It computes per-side calibration diagnostics from the same arrays it reports, can display pooled ECE for directly commensurable definitions even when calibration fails, and withholds pooled ECE for non-commensurable definitions. Its pooled ECE does not imply typed authorization or upgrade the Structural conformance boundary.

Run `uv run mypy` for the strict semantic file set. The checker covers `isoprax/commensurability.py`, `isoprax/semantic_types.py`, `isoprax/evaluation.py`, and `isoprax/admission.py`. The configured exception is limited to missing third-party typing metadata for SciPy and scikit-learn imports; the checked modules' own definitions remain strict.

## Limits

Python's static types cannot prove that JSON/database values share the same definition ID or semantic content. A marker class is a code-level declaration used to statically align evidence types; runtime factories compare the actual IDs and normalized definition digests. Sample digests prevent swapping arrays after calibration but do not independently prove external sample provenance. Callers can deliberately bypass static checks with `Any`, casts, untyped code, or private module internals, so the API also validates evidence at runtime.

The CI oracle independently checks direct commensurability, normalized definition-content identity, calibration policy and sample binding, and pooled authorization. QuickCheck properties, compile-fail evidence examples, and shared Python/Haskell fixtures run when those semantic paths change. The broader Haskell admission, benchmark, and runtime surface remains archived in [the experiment record](../specs/042-haskell-semantics-kernel/assessment.md).

## Assessment

This is a correctness improvement, not only an annotation pass. The strict checker exposes normalized stored fields and finite decision states, and typed authorization makes required evidence explicit in its signature. Review also found and fixed Python issues involving reused samples, retained observations, empty definitions, same-ID changed semantics, policy mismatch, direct observation-process construction, and mixed-threshold sorting. The retained Haskell oracle adds implementation diversity to the shared semantic fixtures while remaining outside runtime paths; CI results are required before calling the change verified.
