# Data Model: Stage 1 Corpus Admission

- **CorpusRow**: One record containing score-time feature snapshot, lineage
  identifiers, split assignment, and outcome class.
- **LineageChain**: Immutable identifier chain linking change, build/deployment,
  and observation records.
- **OutcomeClass**: Enumerated class `observed_positive`,
  `observed_negative`, or `censored` with explicit censor reason.
- **SplitDefinition**: Chronological boundaries for `train`,
  `calibration_fit`, `calibration_gate`, and `test`, frozen before fitting.
- **AdmissionProfile**: Declares allowlisted prediction-time fields,
  forbidden fields, horizon rule, and adequacy thresholds.
- **AdmissionGateResult**: Deterministic pass/fail artifact containing
  gate-by-gate evidence and failed-gate reasons.
- **AdmissionManifest**: Publishable metadata containing split boundaries,
  class counts, horizon declaration, release scope, and provenance summary.
- **CalibrationEvidence**: Non-empty row identifiers showing calibration fitting
  used only `calibration_fit` rows and gating used only `calibration_gate` rows.
- **PredeclarationEvidence**: Hash, external anchor reference, and ordered
  predeclaration/corpus-collection timestamps for frozen horizon and thresholds.
- **CorpusProvenance**: Source identity and explicit private-production and
  privileged-telemetry exclusions required for admissibility.
