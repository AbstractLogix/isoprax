# Implementation Plan: IsoPrax Research-Scope Refinement

**Branch**: `codex/045-research-scope-refinement` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/045-research-scope-refinement/spec.md`

## Summary

Deliver a public, evidence-bounded scope audit and research plan. Update the README so readers see the research mission before the implementation stages. Add linked research documents for program boundaries, outcome/evidence commensurability, operation-specific validity, an invalid-aggregation benchmark, a shared-model experiment, and falsification criteria. Do not change application code or move existing work.

## Technical Context

**Language/Version**: Markdown documentation; the existing reference implementation uses Python 3

**Primary Dependencies**: Existing repository specifications and research artifacts; primary research papers linked from the new documents

**Storage**: Repository files

**Testing**: Editorial review of claims, paths, and cross-links; no test task is requested

**Target Platform**: Git repository and rendered Markdown viewers

**Project Type**: Public research documentation for a reference implementation

**Performance Goals**: Not applicable

**Constraints**: Follow the project constitution; preserve the v0.3 POC and current evidence boundaries; use public sources; preserve unrelated working-tree changes; do not add runtime policy or private product details

**Scale/Scope**: One scope report, one research map, seven focused research documents, one README update, and the Spec Kit record for this documentation feature

## Constitution Check

- **Specification Authority**: PASS. The report treats the v0.3 POC as authoritative for current conformance claims. New research proposals do not rewrite the normative specification.
- **Honest Conformance**: PASS. Synthetic, public-data, and replay evidence retain their existing limits. New hypotheses are labeled.
- **Contract-First Testing**: PASS. No new runtime behavior or normative code rule is introduced, so no implementation tests are required in this feature.
- **Deterministic Core, Explicit Effects**: PASS. No code or runtime effect changes.
- **Minimal Reference Scope**: PASS. No new product runtime, data adapter, or evidence-combination engine is added.

## Design Decisions

1. Separate outcome-commensurability evidence already in the repository from the proposed generalization to evidence commensurability.
2. Assess operations individually. Do not assign one universal evidence score or presume a scalar commensurability grade.
3. Treat the existing `OutcomeDefinition` gate as a bounded reference rule. It compares event, observation process, window, and thresholds; it does not assess every property needed for every evidence operation.
4. Reuse the existing synthetic pooling-harm fixture as a research case, but document that its seven-day and ninety-day windows differ. Do not call those definitions the same event without qualification.
5. Keep the current JEPA code as a bounded shared-predictor reference slice. Describe the multi-family experiment as planned work, not a completed result.
6. Put no current code in the `MOVE TO PRIVATE PROJECT` or `DEPRECATE` categories without direct evidence of private product behavior or redundant/unmaintained functionality.

## Research Sources and Claims

See [research.md](research.md). It separates repository evidence, primary literature, and hypotheses. The literature offers bounded foundations for forecast calibration, subgroup calibration, measurement comparability, distribution shift, and dependent evidence. It does not establish a general IsoPrax evidence-commensurability calculus.

## Research Data Model

See [data-model.md](data-model.md). The document defines conceptual records for claims, assessments, benchmark cases, experiment protocols, and module dispositions. These are research vocabulary only; they are not a public runtime schema.

## Public Interfaces

No software API or command contract is added. The operation table in `docs/research/operation-specific-commensurability.md` is a research proposal, not an enforceable runtime contract.

## Project Structure

### Documentation (this feature)

```text
specs/045-research-scope-refinement/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
└── checklists/requirements.md
```

### Public research outputs

```text
README.md
docs/research/README.md
docs/research/project-scope-and-architecture.md
docs/research/evidence-commensurability.md
docs/research/operation-specific-commensurability.md
docs/research/invalid-aggregation-benchmark.md
docs/research/shared-model-commensurability-experiment.md
docs/research/isoprax-semadmit-boundary.md
docs/research/isoprax-bouleusis-boundary.md
docs/research/falsification.md
```

**Structure Decision**: Keep public research documents under `docs/research/`. Leave implementation modules and existing specifications in place. Use the map as the entry point rather than creating a second implementation directory or a new software layer.

## Validation

- Check every new cross-link and cited repository path against the current tree.
- Compare current-code statements with the referenced modules and specifications.
- Run a whitespace/diff check. Do not run the test suite because this change adds no runtime code and the user did not request tests.

## Constitution Check After Design

PASS. The design is documentation-only, distinguishes proven claims from hypotheses, and keeps existing conformance claims within the authoritative specification.

## Complexity Tracking

No constitution violations or new runtime complexity.
