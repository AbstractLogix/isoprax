# Research: Commensurability Experiments and Evidence

## Decision 1: Use the deterministic CPU JEPA reference

- **Decision**: Fit one `JEPAWorldModel` on a fixed synthetic training set and use its Change risk and Operational anomaly readouts. Keep the backend identity fixed across target-specific calibration.
- **Rationale**: This reuses the public shared-predictor implementation and directly tests the shared-identity claim without requiring GPU training or external data.
- **Alternatives considered**: The optional EB-JEPA backend adds runtime and device variability without answering a different semantic question. A hand-written model would not test the existing reference identity.
- **Limit**: The generated labels are synthetic and partly constructed from the model's deterministic scores. This is a contract and measurement fixture, not an efficacy estimate.

## Decision 2: Calibrate each target separately

- **Decision**: Fit the existing isotonic calibrator on a fixed calibration split for each target and evaluate on distinct synthetic test rows. Report ECE and Brier score per target.
- **Rationale**: Calibration is relative to the target and sample. One shared encoder does not make separate calibrators or labels equivalent.
- **Limit**: Small synthetic splits can make isotonic estimates unstable. Bootstrap intervals and event counts must remain visible.

## Decision 3: Predeclare only two pooled estimands

- **Decision**: Benchmark A may show the 50:50 mean risk of the two lane-specific events as a named mixture. The same-target control may pool two cohorts with 50:50 weights for the identical target. No other shared-model target metrics are pooled.
- **Rationale**: A numeric value can be mathematically summarized without asserting that the events are identical. Naming the estimand states what the number represents.

## Decision 4: Use a finite policy challenge set

- **Decision**: Compare naive, global-label, metadata-only, and operation-specific rules against explicit synthetic cases spanning comparison, ranking, pooling, transfer, averaging, and evidence combination.
- **Rationale**: Each rule and expected case result can be inspected. False permission and unnecessary refusal have direct denominators.
- **Limit**: The case set is authored from the proposed contract. It is not independent adjudication and cannot estimate field error rates. Report any simpler rule that matches the operation-specific rule on this set.

## Decision 5: Quantify uncertainty with deterministic bootstrap intervals

- **Decision**: Use 500 percentile bootstrap resamples with a fixed seed for event rate, ECE, Brier score, and AUC. Skip AUC resamples that contain one class and report the usable count.
- **Rationale**: A fixed nonparametric resampling method makes uncertainty computation reproducible and exposes small-sample variation.
- **Limit**: These intervals quantify variation under the synthetic sample generator. They do not cover model, generator, or real-world uncertainty.

## Literature boundary

Use the primary sources already cited in [the evidence research note](../../docs/research/evidence-commensurability.md). They support target-relative scoring, subgroup calibration, bounded measurement comparability, shift evaluation, and dependence-aware evidence combination. They do not establish that IsoPrax's operation table is complete or that operation-specific gating improves deployed decisions.
