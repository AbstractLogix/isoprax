# Shared-Model, Multiple-Outcome Experiment

**Status**: Executed synthetic experiment. Results are in [the experimental evidence report](experimental-evidence.md) and [machine-readable output](experimental-results.json).

## Question

Does one shared model identity justify comparing, ranking, or pooling forecasts when its outputs refer to different outcome definitions or prediction horizons?

## Hypothesis and controls

- **H1**: A shared encoder, model identity, or JEPA backend does not by itself establish common outcome semantics.
- **H2**: Family-local calibration can coexist with an invalid cross-family comparison.
- **H3**: A global calibration or score summary can hide a family-local error or become dependent on a chosen mixture weight.
- **Positive control**: Use two independent synthetic cohorts with the same operational event, observation process, one-hour window, and threshold. Declare equal cohort weights before pooling.
- **Horizon control**: Use the same synthetic operational observations and event class with one-hour and 24-hour windows. Treat them as separate targets.

## Design

1. Use the existing deterministic JEPA backend identity for the Change risk and Operational anomaly readouts. Fit a separate isotonic calibrator for each target. This run uses fixed synthetic predictor inputs and does not require an external world model.
2. Define a synthetic Change target for a fix-linked defect within 30 days and a synthetic Operational target for a telemetry threshold breach within one hour and within 24 hours. Record the event, observation process, horizon, and threshold for each.
3. Generate deterministic synthetic training, calibration, and test rows. Use 240 calibration and 300 held-out rows for each target. No row crosses that target's calibration/test boundary.
4. Preserve family, event, observation process, threshold, and window in each target definition. Compute target-local ECE, Brier score, ROC AUC when meaningful, event counts, bootstrap intervals, and top-20% ranking summaries.
5. Do not pool different-family or different-horizon metrics. Pool the same-target positive control only as an equally weighted mixture of the two named synthetic cohorts.
6. Run the same-target and different-horizon cases with the same model identity so target identity is not confounded with backend identity.

## Outcomes to inspect

- Target-local calibration, Brier score, discrimination, event counts, and bootstrap uncertainty.
- Score ranking and top-20% selection by target, plus a labeled diagnostic of unsupported cross-target ranking.
- Pooled metrics only for the predeclared same-target 50:50 cohort mixture.
- A descriptive top-20% selection by target and how a diagnostic global ranking reallocates selected cases.
- A 50:50 same-target cohort pool under its named estimand.

The current run does not test calibration transfer, population shift, model-version change, evidence dependence, or operational decision loss. Those remain future experiments.

## Future falsification rule

The shared-model hypothesis is weakened if aligned and misaligned targets behave equivalently under predeclared operations across held-out settings, and simple metadata or naive aggregation produces the same valid interpretations and decisions. The operation-specific proposal is not useful if its assessments do not change validity judgments, ranking, or downstream decisions beyond a simpler rule.

Before data collection, define a minimum meaningful effect, error bars, sample adequacy, and the primary comparison. Do not set these after seeing the result.

## Evidence boundary

This experiment tests whether shared model identity establishes target equivalence, not whether JEPA is a superior predictor. The synthetic labels depend on the deterministic score generator. The result is not real-world efficacy or Semantic/Full Conformance. See the report for numerical results and limits.
