# Research Notes: Public Label-Semantics and Split-Sensitivity Evidence

## Decisions

- Use supplied manifests and fixtures first. Public dataset acquisition and
  adapters are intentionally deferred until source licensing, snapshot identity,
  and reproducibility can be recorded.
- Reuse `OutcomeDefinition` rather than parse free-form label prose. This makes
  comparison structural and prevents wording order from becoming a semantic
  decision.
- Treat split and adaptation metadata as evaluation provenance, not as evidence
  that two outcomes are commensurable.
- Keep the report claim boundary narrower than Semantic Conformance: it records
  evidence about published labels and procedures only.

## Existing repository evidence

- `isoprax/public_label_evidence.py` already reduces source availability,
  licensing, and identity checks to reproduced/blocked/inconclusive states.
- `isoprax/commensurability.py` already owns structured Outcome Definitions and
  graded comparison concepts.
- Stage 0 and Stage 1 documentation prohibit converting calibration or public
  metadata into semantic or predictive claims.

## Deferred questions

- Which published SZZ/JIT sources can be redistributed or represented through
  checksummed metadata without violating terms?
- Which raw observations are retained by each source and can support a valid
  window/threshold bridge?
- How should model retraining cadence and model lineage be represented once a
  real evaluation package exists?

These remain explicit research questions, not hidden assumptions in this slice.
