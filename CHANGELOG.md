# Changelog

All notable changes to this reference implementation are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- A deterministic NumPy JEPA unified-predictor reference slice with shared
  latent state, action-conditioned prediction, and separate Change and
  Operational readouts.
- An optional PyTorch EB-JEPA-style backend with explicit CPU/CUDA selection,
  EMA target encoding, anti-collapse diagnostics, runtime device metadata, and
  fail-closed GPU architecture validation.
- A per-family efficacy evaluator requiring disjoint held-out labeled data, a
  named baseline, frozen thresholds, validated training/run provenance, and
  complete evidence before it can return `efficacy_supported`.
- Focused conformance tests and Spec Kit artifacts for both feature slices.
- A torch-blocked base-import check and a regression test proving EB-JEPA
  anti-collapse weights affect trainable predictions.
- Digest-backed provenance gates for semantic and efficacy evidence, plus report
  validation that preserves the protected per-family evidence floor.
- Bound semantic and efficacy provenance to verifier-produced external-anchor
  statements, including non-empty outcome-definition identities.
- A real production Sigstore/Rekor bundle fixture with offline verifier
  coverage while keeping non-Isoprax predicates rejected.
- Explicit listing and human-selected repair for ambiguous legacy SQLite
  outcome rows.
- Deterministic bootstrap outcome-yield reporting with explicit
  no-positive/no-finite-estimate status for the current pilot.

### Changed

- Exported the JEPA, EB-JEPA, and efficacy-gate APIs from the package surface
  without requiring PyTorch for base-package imports.
- Added the optional `gpu` dependency extra and refreshed the lockfile.
- Made malformed efficacy evidence fail closed as report reasons rather than
  raising during metric evaluation.
- Included a canonical per-family test-row identity digest in efficacy results so
  the report scope cannot silently change under identical aggregate metrics.
- Corrected EB-JEPA readout provenance to identify the online post-state encoder
  used by anomaly scoring and hardened malformed outcome conversion.
- Replaced the broken CLI attestation subprocess with Sigstore's Python
  signing API and one canonical in-toto Statement definition.
- Removed the Sigstore minor-version private-field dependency from Rekor
  reference extraction.
- Pinned GitHub Actions by commit and restricted workflow permissions.
- Raised the default Stage 2 corpus gate to 800 test rows with at least 50
  positive and 50 negative outcomes per family; small smoke tests must now
  override those floors explicitly.

### Documentation

- Recorded local RTX 5070 (`sm_120`) validation with PyTorch 2.14.0+cu130 and a
  passing CUDA smoke test.
- Clarified that GPU execution, synthetic fixtures, and runtime smoke tests do
  not establish predictive efficacy, Semantic Conformance, or Full Conformance.
- Recorded that the historical Stage 2 whoami pilot remains unanchored and all
  three observed outcomes remain negative; no feasibility, corpus, or
  conformance claim is published from it.

### Validation

- Full suite: 410 passed, 1 skipped; total coverage 95.08%.
- Ruff, formatting, pre-commit, and staged-diff checks passed.

No predictive efficacy claim is made in this release entry; real labeled
held-out evidence remains required.

## [0.2.0] - 2026-09-12

### Added

- Sigstore DSSE and Rekor inclusion verification before Stage 2 can emit
  replay-feasibility evidence.
- Calibration controls for evaluation diagnostics.

### Changed

- Made SQLite signal and outcome linkage include `strategy_version`, rejecting
  ambiguous legacy rows and reads.
- Replaced Python-specific identity serialization with RFC 8785 canonical JSON
  so hashes are independently reproducible across languages.
- Made the per-module coverage gate fail closed when a production module is
  absent from coverage data.
- Clarified the injected runner's synthetic scope and its production boundary.

## [0.1.0] - 2026-09-05

### Added

- Initial Isoprax v0.3 reference implementation release.
- Stage 1 admission and public-data evidence infrastructure.
- Bounded Stage 2 replay-feasibility and corpus-evaluation reducers.
