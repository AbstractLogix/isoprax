# Research: JEPA Unified Predictor

## Decisions

### Use a deterministic linear latent predictor for the reference backend

- **Decision**: Encode structured change features and numeric state windows into
  fixed-dimensional vectors, then fit a ridge-regularized linear predictor from
  `(pre_state_embedding, change_embedding)` to `post_state_embedding`.
- **Rationale**: The repository already has NumPy and a strategy abstraction, but no
  GPU runtime or selected deep-learning backend. This proves the action-conditioned
  representation contract without adding an unbounded dependency or an unsupported
  efficacy claim.
- **Alternatives considered**: Forking EB-JEPA or adding a neural framework was
  rejected for this slice because the attached spec leaves the backbone and
  hyperparameters open and the project is production-only/PoC scoped. The public
  strategy interfaces keep that replacement possible later.

### Use deterministic hashed change features and normalized state statistics

- **Decision**: Encode the change diff/message when present and always include
  normalized structured change metrics. Encode each state window using ordered
  values plus stable summary features, while requiring one fixed dimension per
  backend.
- **Rationale**: `ChangeEvent.features` is the existing extensibility boundary and
  `MetricSample` is the existing operational event type. Stable hashing avoids a
  learned vocabulary, network calls, and fit-order dependence.
- **Alternatives considered**: A tokenizer or external code-embedding service was
  rejected because no provider or model artifact is part of the request.

### Keep calibration outside the backend

- **Decision**: Readout adapters accept the existing `Calibrator`; the backend only
  emits deterministic raw values and stable provenance.
- **Rationale**: The feature explicitly requires existing calibration and admission
  code to remain unchanged. This also keeps calibration evidence separate from
  self-supervised pretraining.
- **Alternatives considered**: Embedding calibration state into the predictor was
  rejected because it would blur pretraining and label-dependent evaluation.

### Make Semantic eligibility an evidence gate, not a constructor flag

- **Decision**: Expose a report that defaults to Structural and accepts a structured
  evidence record only after validating backend identity, shared representation
  identity, non-decomposability, and non-trivial finite readout evidence.
- **Rationale**: A boolean assertion would violate the project's provenance and
  honest-conformance rules. Calibration alone cannot establish semantic identity.
- **Alternatives considered**: An `semantic=True` option was rejected as
  caller-controlled unsupported evidence.

## Research Boundary

The attached document names ACT-JEPA, LLM-JEPA, EB-JEPA, and MTS-JEPA as design
references. This implementation records their role as supplied context but does not
reconstruct or claim equivalence to those papers. Empirical backend selection,
GPU training, window/horizon selection, and real replay corpus evidence remain
follow-up work.
