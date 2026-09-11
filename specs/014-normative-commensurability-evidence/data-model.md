# Data Model: Normative Authority and Commensurability Evidence

## NormativeCitation

- `source_path`: repository-relative implementation file.
- `line`: positive source line number.
- `reference`: full section identifier such as `5.6.3`, `8.2`, or `D.3`.
- `resolved_target`: numbered heading/anchor in the vendored specification.
- `status`: `resolved` or `unresolved`.

Validation: references must use the supported section grammar, preserve
subsections and appendix identifiers, and resolve to exactly one normative
target.

## OutcomeDefinition

- `id`: stable identifier.
- `event`: canonical event identity.
- `observation_process`: structured process kind and parameters.
- `window`: duration plus anchor semantics.
- `thresholds`: ordered or unordered typed threshold terms, each with metric,
  operator, value, and optional sustain duration.
- `description`: human-readable explanation, excluded from comparison.

Validation: canonical serialization must be deterministic; semantically
unordered collections are normalized; malformed operators, durations, or
missing required process parameters are rejected.

## Attestation

- `attestor`: named person or organization.
- `justification`: non-empty explanation of equivalence.
- `left_definition_id`, `right_definition_id`: definitions covered.
- `provenance`: stable reference to the evidence supporting the attestation.

Validation: no empty fields; an attestation cannot erase an event or
observation-process mismatch without evidence explicitly supporting it.

## CommensurabilityAssessment

- `level`: `direct`, `attested`, `bridgeable`, or `irreducible`.
- `left_id`, `right_id`: compared definitions.
- `differing_fields`: deterministic sorted field names.
- `reason`: human-readable explanation.
- `attestation` or `bridge`: optional evidence record required by its level.
- `pooling_allowed`: true only for direct/attested equivalence under the
  declared policy; false for bridgeable until transformation is applied and
  false for irreducible.

## CalibrationDiscriminationReport

- `calibration`: ECE, Brier score, sample count, bins, threshold, and status.
- `discrimination`: AUC, score variation, class counts, and status.
- `declaration`: `qualified`, `uncalibrated`, or `inconclusive`.
- `reason`: explicit gate explanation.

Validation: qualified requires calibration pass, both outcome classes, enough
events, non-zero score variation, and valid AUC; absent metrics never default
to pass.

## PoolingHarmEvidence

- `shared_event_ids`: identical event population for both families.
- `left_window`, `right_window`: seven-day and ninety-day definitions.
- `left_ece`, `right_ece`, `pooled_ece`: descriptive calibration metrics.
- `k`: deterministic selection size.
- `per_family_selection`, `pooled_selection`: selected IDs.
- `selection_metric`: deterministic per-definition outcome metric.
- `degradation`: per-family minus pooled result, so positive values mean pooled
  ranking lost per-family top-k precision.
- `claim_boundary`: explicit non-efficacy/non-conformance statement.

## PublicLabelEvidence

- `manifest_version` and `sources`: source IDs, versions, licenses, retrieval
  dates/identifiers, and checksums where available.
- `definitions`: the two published label definitions and observation processes.
- `aligned_event_ids`: nominally shared events.
- `disagreement_summary`: counts and differences.
- `status`: `reproduced`, `blocked`, or `inconclusive`.
- `claim_boundary`: prohibition on real-world conformance claims.
