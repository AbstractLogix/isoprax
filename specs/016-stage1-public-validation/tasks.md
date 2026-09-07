---
description: "Implementation tasks for complete Stage 1 public-data validation"
---

# Tasks: Complete Stage 1 Public-Data Validation

## Phase 1: Contract and adapter

- [X] T001 Add the frozen Stage 1 predeclaration with source references, licenses, split boundaries, outcome rules, and claim boundary.
- [X] T002 Implement deterministic ApacheJIT and Google Trace v1 adapters using existing admission/per-family contracts.
- [X] T003 Implement source hash verification, schema validation, and fail-closed missing/changed-source handling.
- [X] T004 Implement aggregate report serialization with separate family records and no pooled metrics.

## Phase 2: Verification and evidence

- [X] T005 Add fixture tests for both adapters, score-time fields, split isolation, source failures, and deterministic identities.
- [X] T006 Run the adapters against the declared public files and write the checked-in aggregate evidence report.
- [X] T007 Run focused/full tests, coverage, lint, and diff checks.
- [X] T008 Update README and Stage 1 convergence documentation with the actual evidence and remaining claim boundary.

## Dependencies

T001 precedes T002–T004. T005 follows adapter contracts. T006 depends on the external source files being available. T007–T008 follow implementation and the live run.
