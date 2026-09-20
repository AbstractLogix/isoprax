# Data Model: EB-JEPA GPU Backend and Efficacy Gate

## `EBJEPAConfig`

Immutable configuration for embedding sizes, hidden width, epochs, batch size,
learning rate, EMA decay, regularization weights, seed, and explicit device. Its
identity is included in the backend identity.

## `EBJEPATrainingReport`

Completed-run evidence: pair count, input and embedding dimensions, requested and
actual device, PyTorch/CUDA metadata, seed, final prediction/regularizer losses,
finite/completed status, backend identity, and claim boundary.

## `EfficacyEvaluationProfile`

Predeclared policy: corpus/split identity, baseline identity, minimum test rows and
positive/negative counts per family, minimum AUC improvement, maximum allowed ECE,
threshold version, and evidence class (`synthetic` or `real_labeled`). It is
immutable and hashed into the report identity. Real-labeled evidence also carries
an independently identified, digest-backed, externally verified `EvidenceProvenance`
artifact tied to the corpus and split identities. Only verified `real_labeled`
evidence can produce `efficacy_supported`.

## `FamilyEfficacyResult`

One-family test result: family and outcome-definition IDs, candidate/baseline AUC,
Brier, ECE, counts, threshold comparisons, and unavailable-evidence reasons.

## `EfficacyReport`

Top-level decision with status `not_claimable` or `efficacy_supported`, scoped model,
corpus, split, baseline, training-report, run-configuration, and profile identities,
the serialized frozen profile and configuration, per-family results, reasons, and a
claim boundary. It recomputes its identity and never contains a pooled score for
non-commensurable families.

## Invariants

- Device, seed, configuration, and split metadata are explicit.
- A supported report contains a validated completed training report whose backend
  identity matches the model identity.
- A supported report contains a canonical run configuration whose backend identity
  matches the model identity.
- A claimable profile cannot lower the protected 800-row, 50-positive, and
  50-negative per-family evidence floor.
- Row IDs across train, calibration, and test partitions are pairwise disjoint.
- Test scores and labels are aligned, binary, finite, and within probability bounds.
- A report is `efficacy_supported` only when every required family passes every gate.
- Missing evidence is represented by a reason, never by zero, neutral, or guessed data.
