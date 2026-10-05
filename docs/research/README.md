# IsoPrax Research Map

IsoPrax is an open research and reference framework for measurement validity,
calibration, outcome semantics, and valid operations on predictions and other
evidence. Its main question is: **What does each result measure, and which
operations on those results does the evidence support?**

## Start here

1. [Scope and architecture audit](project-scope-and-architecture.md): current
   mission, module dispositions, contribution, and next research question.
2. [Evidence commensurability](evidence-commensurability.md): evidence types,
   hypotheses, literature, and open questions.
3. [Operation-specific commensurability](operation-specific-commensurability.md):
   provisional conditions for comparison, ranking, pooling, transfer, and
   fusion.
4. [Invalid aggregation benchmark](invalid-aggregation-benchmark.md): a
   reproducible synthetic counterexample and valid control.
5. [Shared-model experiment](shared-model-commensurability-experiment.md): a
   protocol to test whether one model identity supports cross-target
   operations.
6. [Falsification and stop conditions](falsification.md): measurable results
   that would narrow or reject the research claims.

## Program boundaries

- [IsoPrax and Semadmit](isoprax-semadmit-boundary.md) defines the public
  research to private enforcement boundary.
- [IsoPrax and Bouleusis](isoprax-bouleusis-boundary.md) defines the public
  validity assessment to private deliberation boundary.

IsoPrax specifies and tests evidence conditions. It does not choose beliefs,
hypotheses, plans, experiments, or actions.

## Existing foundation

- [Authoritative v0.3 POC](../isoprax-v0.3-poc.md) and
  [source provenance](../isoprax-v0.3-poc-provenance.md) define the reference
  baseline.
- [Calibration Is Not Enough](<Calibration Is Not Enough_ Outcome Commensurability as a Precondition for Cross-Family Failure Prediction.md>)
  states the current cross-family outcome thesis and its limits.
- [Feature 014](../../specs/014-normative-commensurability-evidence/spec.md)
  records normative commensurability evidence.
- [Feature 036](../../specs/036-jepa-unified-predictor/spec.md) and
  [Feature 037](../../specs/037-eb-jepa-gpu-efficacy/spec.md) record the shared
  predictor reference and its separate efficacy gate.
- [Public dataset decisions](../../examples/public-datasets/decision-ledger.json),
  [Stage 1 validation](../stage1/stage1-public-validation.json), and
  [Feature 044](../../specs/044-public-dataset-lane-qualification/spec.md)
  track distinct source-specific evidence lanes.

These records are complementary. A common format, calibration method, public
availability, or model identity does not establish a common outcome or valid
cross-source operation.

## Claim labels

| Label | Meaning |
|---|---|
| **Established in this repository** | Implemented structural behavior or a result from a named synthetic or source-specific fixture. Claims stay within that scope. |
| **Supported by primary literature** | A result established for the cited research setting. It motivates questions; it does not directly prove IsoPrax's broader thesis. |
| **Hypothesis or proposal** | A rule, experiment, or boundary that still needs testing. It is not a conformance result. |

## Research path

1. Reproduce the current synthetic counterexample and retain the declared
   outcome and window for each lane.
2. Compare it with the same-target control in the benchmark protocol.
3. Test one shared predictor across multiple named outcomes, with a same-target
   control and separate target-level reports.
4. Compare operation-specific assessments with simple and naive alternatives.
5. Extend only to public data with explicit provenance and a valid observation
   process. Keep source-specific outcomes separate where their meanings differ.
6. Publish negative as well as positive results. Apply the stated stop
   conditions before making broader claims.
