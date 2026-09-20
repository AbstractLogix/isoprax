# Data Model: JEPA Unified Predictor

## `JEPATrainingPair`

Represents one self-supervised example.

| Field | Type | Rules |
|---|---|---|
| `change` | `ChangeEvent` | Required; supplies the action representation. |
| `pre_state` | sequence of finite numeric rows | Required; non-empty and fixed dimensional within the backend. |
| `post_state` | sequence of finite numeric rows | Required; non-empty and same row width as `pre_state`. |

Rows are ordered in time. The implementation does not include labels in this
entity; labels enter only through optional readout-head/calibrator fitting.

## `JEPABackendConfig`

Immutable configuration for representation dimensions and fitting regularization.
The dimensions and regularization must be positive finite values. The config is part
of the backend identity.

## `JEPATrainingReport`

Immutable fit evidence containing pair count, input/representation dimensions,
finite mean latent prediction error, backend identity, and state representation
identity. It reports training evidence only, not predictive efficacy.

## `JEPASemanticEvidence`

Evidence supplied by an evaluation workflow, containing backend identity, state
representation identity, a backend-derived shared-representation proof,
`non_decomposable`, finite non-constant JIT and AIOps readout values, and the
sample count used. The validator rejects mismatches or degenerate evidence.

## `JEPAAssessment`

Immutable conformance report. The default tier is `Structural`; `Semantic` is
returned only when `JEPASemanticEvidence` validates against the fitted backend.
The report always includes a claim boundary and reasons.

## Readout adapters

- `JEPARiskStrategy` implements the existing `RiskStrategy` contract and emits
  `RiskSignal` with `JEPA_DEFECT_RISK`.
- `JEPAAnomalyStrategy` implements the existing `AnomalyStrategy` contract and
  emits `AnomalySignal` with `JEPA_OPERATIONAL_FAILURE`.

Both hold the same `JEPAWorldModel` instance. They do not copy predictor parameters.
