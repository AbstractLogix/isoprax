---
description: "Implementation tasks for the Stage 2 corpus evaluation gate"
---

# Tasks: Stage 2 Corpus Evaluation Gate

## Phase 1: Contracts

- [ ] T001 Define immutable corpus-evaluation profile and report entities.
- [ ] T002 Define canonical row, split, metric-input, and claim-boundary hashes.
- [ ] T003 Add constructor and provenance rejection tests.

## Phase 2: Corpus integrity

- [ ] T004 Validate terminal-record linkage and denominator preservation.
- [ ] T005 Reject duplicate revisions, split leakage, post-score fields, and
  mutable lane metadata.
- [ ] T006 Add temporal split and exclusion reporting.

## Phase 3: Family evaluation

- [ ] T007 Add per-family calibration and discrimination summaries.
- [ ] T008 Add score variance/non-degeneracy gate and constant-predictor tests.
- [ ] T009 Require declared positive/negative/sample thresholds before
  qualified metrics.
- [ ] T010 Reject incompatible pooling and preserve commensurability reasons.

## Phase 4: Public report

- [ ] T011 Implement deterministic report serialization and validation.
- [ ] T012 Add evidence-release and withheld-claim tests.
- [ ] T013 Update README/demo with the new boundary, without Semantic claims.

## Phase 5: Convergence

- [ ] T014 Run focused and full validation gates.
- [ ] T015 Complete `converge.md` and review the branch against `spec.md`.
