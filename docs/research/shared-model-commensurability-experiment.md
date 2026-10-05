# Shared-Model, Multiple-Outcome Experiment

**Status**: Proposed experiment. No new experiment was run for this document.

## Question

Does one shared model identity justify comparing, ranking, or pooling forecasts when its outputs refer to different outcome definitions or prediction horizons?

## Hypothesis and controls

- **H1**: A shared encoder, model identity, or JEPA backend does not by itself establish common outcome semantics.
- **H2**: Family-local calibration can coexist with an invalid cross-family comparison.
- **H3**: A global calibration or score summary can hide a family-local error or become dependent on a chosen mixture weight.
- **Positive control**: Give both output heads the same event definition and observation process, while allowing different conditioning features. Check that the target and operation are aligned before comparing the scores.
- **Horizon control**: Keep the event class fixed but change the forecast horizon. Treat “within one hour” and “within one day” as separate events unless the experiment defines a valid transformation to a shared target.

## Design

1. Use one declared model identity with two output heads. Start with the existing deterministic JEPA reference path or a fixed synthetic predictor; do not require a proprietary world model.
2. Define a Change target such as a repository-derived defect label and an Operational target such as a telemetry threshold breach. State source, event, observation process, horizon, threshold, censoring, and model version for each.
3. Generate or acquire separate, provenance-backed examples. Keep any common identifier linkage distinct from evidence that the two labels represent the same event.
4. Predeclare train, calibration, and held-out splits by system or source group. Prevent repeated revisions, deployment observations, or shared source rows from crossing splits.
5. Set minimum sample and event-count requirements from the intended calibration precision. Do not claim a conformance tier from a synthetic sample-size target.
6. Preserve family and outcome identity through all reports. Compute per-family calibration, Brier score, discrimination, uncertainty intervals, and decision metrics first.
7. Compute pooled metrics only for an explicitly declared mixture target and predeclared weights. Compare them with family-specific summaries.
8. Run the positive control and horizon control with the same model identity so model identity is not confounded with target alignment.

## Outcomes to inspect

- Family-local calibration and reliability curves.
- Pooled diagnostics under at least two declared mixture weights.
- Score ranking and top-k selection by family and after pooling.
- Calibration transfer from each family to the other, with no transfer, calibrated transfer, and a metadata-only control.
- Decision loss under a named, predeclared decision rule; keep the rule separate from IsoPrax validity assessment.
- Results after a controlled population shift or model-version change.
- Whether a shared-source dependency changes uncertainty or evidence combination.

## Falsification rule

The shared-model hypothesis is weakened if aligned and misaligned targets behave equivalently under predeclared operations across held-out settings, and simple metadata or naive aggregation produces the same valid interpretations and decisions. The operation-specific proposal is not useful if its assessments do not change validity judgments, ranking, or downstream decisions beyond a simpler rule.

Before data collection, define a minimum meaningful effect, error bars, sample adequacy, and the primary comparison. Do not set these after seeing the result.

## Evidence boundary

This experiment tests the meaning of outputs, not whether JEPA is a superior predictor. A shared-model result from synthetic data is not real-world efficacy or Semantic/Full Conformance. Report each target and its calibration separately unless the experiment establishes and predeclares a common outcome.
