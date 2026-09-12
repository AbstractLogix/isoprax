---
description: "Implementation tasks for the Stage 2 corpus evaluation gate"
---

# Tasks: Stage 2 Corpus Evaluation Gate

## Phase 1: Contracts

- [X] T001 Define immutable corpus-evaluation profile and report entities.
- [X] T002 Define canonical row, split, metric-input, and claim-boundary hashes.
- [X] T003 Add constructor and provenance rejection tests.

## Phase 2: Corpus integrity

- [X] T004 Validate terminal-record linkage and denominator preservation.
- [X] T005 Reject duplicate revisions, split leakage, post-score fields, and
  mutable lane metadata.
- [X] T006 Add temporal split and exclusion reporting.

## Phase 3: Family evaluation

- [X] T007 Add per-family calibration and discrimination summaries.
- [X] T008 Add score variance/non-degeneracy gate and constant-predictor tests.
- [X] T009 Require declared positive/negative/sample thresholds before
  qualified metrics.
- [X] T010 Reject incompatible pooling and preserve commensurability reasons.

## Phase 4: Public report

- [X] T011 Implement deterministic report serialization and validation.
- [X] T012 Add evidence-release and withheld-claim tests.
- [X] T013 Update README/demo with the new boundary, without Semantic claims.

## Phase 5: Convergence

- [X] T014 Run focused and full validation gates.
- [X] T015 Complete `converge.md` and review the branch against `spec.md`.

## Phase 6: Evidence-scale defaults

- [X] T016 Raise the global corpus profile defaults to 800 test rows and 50
  positive/negative outcomes per family.
- [X] T017 Make all small structural fixtures explicitly override the evidence
  scale and document the intentional calibration-floor override.
