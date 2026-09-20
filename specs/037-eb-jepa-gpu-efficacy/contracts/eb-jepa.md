# Contract: Optional EB-JEPA Backend and Efficacy Report

## Optional backend

`EBJEPAWorldModel` MUST expose:

- `fit(pairs)` returning a finite `EBJEPATrainingReport`;
- `backend_identity`, `state_representation_identity`, `is_fitted`, and
  `training_report` properties;
- `predict_post`, `raw_change_risk`, `raw_anomaly_score`, and shared readout
  provenance compatible with the existing JEPA strategies;
- explicit `device` behavior with no silent CUDA-to-CPU fallback.

The module MUST be importable without importing `torch` until the backend is
constructed or fitted.

## Efficacy evaluator

`evaluate_eb_jepa_efficacy(...)` MUST:

1. validate profile and split identity before reading test metrics;
2. reject missing, overlapping, one-class, non-finite, or constant evidence;
3. compute candidate and baseline per-family AUC/Brier/ECE diagnostics;
4. apply only thresholds present in the immutable profile;
5. reject synthetic/runtime evidence as `not_claimable` even when metric fixtures
   pass;
6. return `not_claimable` with reasons unless every required family passes; and
7. return `efficacy_supported` only with an exact evidence scope and no pooled score
   when definitions are non-commensurable.

The report status is evidence metadata, not a Semantic or Full Conformance upgrade.
