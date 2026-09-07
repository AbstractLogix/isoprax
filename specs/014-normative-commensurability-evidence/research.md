# Research: Normative Authority and Commensurability Evidence

## Decision 1: Keep the normative authority as a repository artifact

- **Decision**: Vendor the authoritative Isoprax v0.3 POC text as a versioned
  Markdown document under `docs/`, preserving numbered sections and appendices.
- **Rationale**: The implementation already cites stable section identifiers;
  a repository-local artifact makes those claims reviewable offline and allows
  a cheap source scan to enforce them.
- **Alternatives considered**: Continue pointing to an external document
  (unverifiable in a checkout); rewrite every citation as prose (loses stable
  traceability); use a generated index without the normative text (does not
  solve authority availability).

## Decision 2: Use canonical structured values for Outcome Definitions

- **Decision**: Represent event identity, window, thresholds, and observation
  process as frozen value objects with canonical serialization. Retain human
  descriptions as explanatory metadata only.
- **Rationale**: Comparison must be invariant to prose ordering and whitespace,
  while preserving enough typed information to distinguish re-derivable from
  irreducible mismatches.
- **Alternatives considered**: Normalize strings only (still creates false
  negatives); compare descriptions (makes human wording normative); introduce
  a general ontology (unnecessary scope for the POC).

## Decision 3: Grade commensurability and require explicit attestation

- **Decision**: Return `direct`, `attested`, `bridgeable`, or `irreducible`
  assessments with field-level reasons. Attestation is data-bearing provenance,
  not a bypass flag; bridgeable results require retained observations and a
  deterministic transformation record.
- **Rationale**: Event identity and observation-process differences can be
  impossible to repair, while window and threshold differences may be
  re-derived. A graded result directly explains why replay is valuable.
- **Alternatives considered**: Preserve a boolean only (loses remediation
  guidance); allow any named attestor to override an event mismatch (unsafe and
  non-falsifiable); automatically infer equivalence from text (not authoritative).

## Decision 4: Use ROC AUC plus a score-variation guard for discrimination

- **Decision**: Report ROC AUC when both outcome classes and sufficient samples
  exist, and independently require non-zero score variation. Missing or
  undefined AUC is an explicit failed/inconclusive qualifier.
- **Rationale**: A constant base-rate predictor can pass ECE but has no ranking
  information. AUC captures ordering while the variation guard makes the
  degenerate case explicit, including tied-score edge cases.
- **Alternatives considered**: Variance alone (does not measure ordering); AUPRC
  alone (depends strongly on prevalence); calibration alone (the defect this
  feature is intended to close).

## Decision 5: Make the pooling-harm result deterministic and synthetic

- **Decision**: Use fixed same-event fixtures with seven-day and ninety-day
  labels, fixed scores, fixed top-k, and a fixed degradation assertion. Report
  pooled ECE as descriptive masking evidence but never as permission to pool.
- **Rationale**: The failure mode must reproduce offline and remain separate
  from real-world efficacy claims.
- **Alternatives considered**: Randomized demo data (flaky); public data as the
  only proof (network/licensing fragile); circular self-comparison (proves
  nothing about harm).

## Decision 6: Treat the public SZZ anchor as an evidence package, not a runtime
dependency

- **Decision**: Record source identifiers, versions, licenses, retrieval facts,
  definition text, aligned event IDs, and comparison outputs in a manifest-driven
  package. Missing or incompatible source material produces blocked/inconclusive
  status.
- **Rationale**: The core tests remain offline and production-safe while the
  real-world example remains independently auditable.
- **Alternatives considered**: Download during tests (non-deterministic and
  network-dependent); silently embed transformed data (weak provenance); add a
  production adapter (outside the feature’s safe scope).

## Decision 7: Add a minimal deterministic ForecastStrategy

- **Decision**: Implement a history-based forecast strategy that emits only a
  `ForecastSignal`, then exercise it through `SQLiteKB` event, definition,
  signal, and retrieval paths.
- **Rationale**: This closes the existing third-strategy gap without changing
  the Signal contract or introducing a learned model.
- **Alternatives considered**: Leave the abstract export untouched (does not
  prove the contract); add a model dependency (unnecessary); overload a risk
  strategy (wrong family and wrong signal semantics).
