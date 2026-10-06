# Implementation Plan: Commensurability Experiments and Evidence

**Branch**: `codex/046-commensurability-experiments` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Approved experimental-phase request and `specs/046-commensurability-experiments/spec.md`.

## Summary

Correct the historical scope audit and project responsibility language. Add one deterministic CPU runner that executes Benchmark A, a three-case shared-JEPA experiment, and a finite operation-gate challenge set. Save canonical JSON results and a linked evidence report. Keep synthetic results separate from established repository evidence and literature claims.

## Technical Context

**Language/Version**: Python 3.10+; Markdown and JSON

**Primary Dependencies**: Existing NumPy, scikit-learn, and IsoPrax JEPA/evaluation modules; no new dependency

**Storage**: Checked-in research report and deterministic JSON result

**Testing**: Focused pytest tests for deterministic outputs, estimand guards, per-target reporting, and gate metrics; run the documented runner twice and compare output

**Target Platform**: Offline CPU execution from the repository root with `uv`

**Project Type**: Public research reference and reproducible synthetic experiment

**Performance Goals**: Complete in a few seconds on a standard CPU; fixed sample counts and bootstrap count

**Constraints**: Synthetic claims only; no cross-target pool without an exact predeclared estimand and weights; preserve Haskell oracle scope; preserve unrelated Feature 044 changes in the other checkout; no runtime admission, deliberation, or orchestration behavior

**Scale/Scope**: One Python runner and focused tests; three experiment sections; one JSON result; updates to linked research documents and this feature record

## Constitution Check

- **Specification Authority**: PASS. The runner is research evidence and does not alter normative v0.3 behavior.
- **Honest Conformance**: PASS. Synthetic targets, calibration, and JEPA identity are not real efficacy, Semantic conformance, or Full Conformance.
- **Contract-First Testing**: PASS. Runner invariants have focused automated tests; the Haskell public-semantics oracle is unchanged.
- **Deterministic Core, Explicit Effects**: PASS. Fixed seeds, stable ordering, no network access, and canonical JSON output.
- **Minimal Reference Scope**: PASS. No trust engine, runtime enforcement, agent state, planning, or new dependency.

## Design Decisions

1. Use the existing deterministic `JEPAWorldModel`, `JEPARiskStrategy`, and `JEPAAnomalyStrategy`. Fit the shared backend once. Fit target-local calibrators only on each target's synthetic calibration split.
2. Use distinct outcome definitions for Change-family, Operational-family, and short/long Operational horizons. Keep a separate same-target cohort control.
3. Report Brier score, ten-bin ECE, ROC AUC when both classes occur, event-rate and metric intervals from deterministic bootstrap resampling, and top-20% ranking summaries. Report the bootstrap seed, count, and interval method.
4. Permit pooled diagnostics only for two exact predeclared estimands: Benchmark A's 50:50 mean of two lane-specific event risks, and the shared-model positive control's 50:50 mixture of two cohorts for the same event definition. Do not label the first a common event.
5. Compare four named policies on a fixed synthetic case table. Treat each case's expected permission and interpretation as declared challenge-set truth, not empirical ground truth. The metadata-only rule reads target and declared-mixture metadata; the operation-specific rule also checks the operation's sample, validation, timing, mapping, and dependence requirements.
6. Measure downstream ranking under a fixed top-20% review-capacity rule. If cross-target ranking is unsupported, the reference behavior ranks within each target. Count selected-record changes against each case's declared expected operation.
7. Treat the small Haskell oracle as-is. Add no oracle API or trust/admission behavior.
8. Correct the scope audit to assess tracked Feature 044 material in the baseline ancestry. Name only the uncommitted GADFPD/RCAEval qualification files as outside that historical tree.

## Research Inputs

The experiment reports existing repository evidence separately from new synthetic results. Adjacent primary literature remains bounded as described in [evidence-commensurability.md](../../docs/research/evidence-commensurability.md): forecast verification and proper scores are target-relative; subgroup calibration, measurement invariance, dataset shift, and dependent-evidence methods do not prove a universal IsoPrax rule.

## Project Structure

```text
isoprax/research_experiments.py
isoprax/operation_gate_experiment.py
tests/test_research_experiments.py
docs/research/experimental-evidence.md
docs/research/experimental-results.json
docs/research/invalid-aggregation-benchmark.md
docs/research/shared-model-commensurability-experiment.md
docs/research/operation-specific-commensurability.md
docs/research/project-scope-and-architecture.md
docs/research/isoprax-semadmit-boundary.md
docs/research/isoprax-bouleusis-boundary.md
```

The Python module exposes deterministic experiment functions and `python -m isoprax.research_experiments`. The checked-in results are generated by the same command documented in the report.

## Validation

Run the focused experiment tests, the existing JEPA and semantic-oracle differential tests, Ruff on changed Python files, and the runner twice. Compare canonical JSON byte-for-byte. Run `git diff --check`, validate links, inspect the final diff, and run the Spec Kit convergence assessment.

## Constitution Check After Design

PASS. The design adds only synthetic research fixtures and reports. It keeps model identity distinct from target identity, requires named mixture estimands for pools, and does not change the public semantics oracle or other project runtime boundaries.

## Complexity Tracking

No constitution exception. Reuse the existing deterministic backend and evaluation dependencies. The fixed challenge set is deliberately narrow; it does not justify a general operation-policy framework.
