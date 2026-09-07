# Implementation Plan: Normative Authority and Commensurability Evidence

**Branch**: `014-normative-commensurability-evidence` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/014-normative-commensurability-evidence/spec.md`

**Note**: This template is filled in by the `$speckit-plan` command; its definition describes the execution workflow.

## Summary

Vendor the numbered Isoprax v0.3 POC authority and make its citations
machine-checkable. Replace prose-based Outcome Definition comparison with
canonical structured values and a graded assessment that preserves an explicit
fail-closed irreducible result. Extend calibration qualification with
discrimination evidence, add a deterministic same-event pooling-harm fixture,
exercise ForecastStrategy through SQLiteKB, and package the public-label anchor
as blocked/inconclusive evidence unless its provenance and license prerequisites
are satisfied.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.10–3.14

**Primary Dependencies**: Existing NumPy, SciPy, scikit-learn, pytest, and the
existing `isoprax` contracts; no new runtime dependency planned

**Storage**: In-memory deterministic fixtures and existing SQLiteKB reference
implementation; vendored Markdown/spec artifacts

**Testing**: Focused pytest conformance tests, demo/evidence checks, `uv run`
commands, and repository coverage gates

**Target Platform**: Offline Linux/WSL and CI execution

**Project Type**: Single-package reference library with executable examples

**Performance Goals**: Deterministic results for small synthetic fixtures;
citation scanning and focused tests remain suitable for ordinary CI latency

**Constraints**: Offline-capable core, no automatic attestation acceptance, no
pooled non-commensurable scores, explicit blocked/censored/inconclusive states,
and no Semantic/Full Conformance claim from this feature

**Scale/Scope**: Existing Stage 0 package, one vendored normative document,
small deterministic fixtures, one concrete ForecastStrategy, and one bounded
public-label evidence manifest

## Constitution Check

| Principle | Design response | Result |
| --- | --- | --- |
| Specification Authority | The vendored numbered document becomes the checked-in citation authority; provenance and unsupported scope remain explicit. | Pass |
| Honest Conformance | Pooling harm and public-label artifacts are evidence about failure modes only; Structural/Semantic boundaries remain fail-closed. | Pass |
| Contract-First Testing | Citation resolution, structured comparison, attestation rejection, calibration degeneracy, pooling harm, and ForecastStrategy round-trip each receive focused tests. | Pass |
| Deterministic Core, Explicit Effects | Comparison, metrics, fixtures, and citation checks are pure for fixed inputs; public data is represented through explicit manifests and blocked states. | Pass |
| Minimal Reference Scope | Changes remain within existing modules/examples/tests and add no production adapters or online services. | Pass |

Pre-design gate: Pass.

## Project Structure

### Documentation (this feature)

```text
specs/014-normative-commensurability-evidence/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── evidence-and-library-contract.md
├── tasks.md
├── converge.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
tests/
isoprax/
├── commensurability.py       # structured definitions and graded comparison
├── evaluation.py             # discrimination/calibration qualification
├── signals.py                # ForecastSignal contract remains score-free
├── strategies.py             # concrete ForecastStrategy seam
├── kb.py                     # SQLite round-trip behavior
└── (new) normative.py        # citation extraction/resolution if needed

docs/
└── isoprax-v0.3-poc.md       # vendored numbered authority and provenance

examples/
└── demo_cross_family.py      # replace circular replay demonstration

tests/
├── test_commensurability.py
├── test_evaluation.py
├── test_forecast_strategy.py
├── test_normative_citations.py
└── test_pooling_harm.py
```

**Structure Decision**: Keep the feature in the existing single-package
reference library. Add only the smallest new domain seams needed for citation
resolution, graded definition comparison, discrimination qualification, and
the deterministic evidence fixtures. Keep public-data retrieval outside the
offline core; its manifest and blocked-state validation are the contract.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
No constitution exceptions required.
