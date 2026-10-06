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
   proposed conditions and results against simpler rules.
4. [Invalid aggregation benchmark](invalid-aggregation-benchmark.md): executed
   deterministic Benchmark A and its valid same-target control.
5. [Shared-model experiment](shared-model-commensurability-experiment.md):
   executed synthetic JEPA tests across event families and horizons.
6. [Experimental evidence report](experimental-evidence.md): results, evidence
   classes, answers, and next research questions.
7. [Machine-readable results](experimental-results.json): exact output from the
   deterministic runner.
8. [Falsification and stop conditions](falsification.md): findings that can
   narrow or reject the research claims.

## Program boundaries

- [IsoPrax and Semadmit](isoprax-semadmit-boundary.md) defines the research to
  runtime admission and verification enforcement boundary.
- [IsoPrax and Bouleusis](isoprax-bouleusis-boundary.md) defines the validity
  assessment to deliberation and epistemic-state boundary.

IsoPrax specifies and tests evidence conditions. It does not choose beliefs,
hypotheses, plans, experiments, or actions.

## Existing foundation

- [Authoritative v0.3 POC](../isoprax-v0.3-poc.md) and
  [source provenance](../isoprax-v0.3-poc-provenance.md) define the reference
  baseline.
- [Calibration Is Not Enough](Calibration%20Is%20Not%20Enough_%20Outcome%20Commensurability%20as%20a%20Precondition%20for%20Cross-Family%20Failure%20Prediction.md)
  states the current cross-family outcome thesis and its limits.
- [Feature 014](../../specs/014-normative-commensurability-evidence/spec.md)
  records normative commensurability evidence.
- [Feature 036](../../specs/036-jepa-unified-predictor/spec.md) and
  [Feature 037](../../specs/037-eb-jepa-gpu-efficacy/spec.md) record the shared
  predictor reference and its separate efficacy gate.
- [Public dataset decisions](../../examples/public-datasets/decision-ledger.json)
  and [Stage 1 validation](../stage1/stage1-public-validation.json) track
  distinct source-specific evidence lanes. New lanes need their own
  qualification before inclusion.

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

1. Reproduce the same-number, different-event benchmark and same-target control.
2. Inspect separate JEPA family and horizon results and the same-target pool.
3. Compare operation-specific gating with naive, global-label, and
   metadata-only alternatives.
4. Extend only to public data with explicit provenance and a valid observation
   process. Keep source-specific outcomes separate where their meanings differ.
5. Publish negative as well as positive results. Apply the stated stop
   conditions before making broader claims.
