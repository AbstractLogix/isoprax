# Changelog

All notable changes to this reference implementation are recorded here.

## [Unreleased]

- The historical Stage 2 whoami pilot remains unanchored and all three
  observed outcomes remain negative; no feasibility, corpus, or conformance
  claim is published from it.
- Replaced the broken CLI attestation subprocess with Sigstore's Python
  signing API and one canonical in-toto Statement definition.
- Added a real production Sigstore/Rekor bundle fixture with offline verifier
  coverage while keeping non-Isoprax predicates rejected.
- Removed the Sigstore minor-version private-field dependency from Rekor
  reference extraction.
- Added explicit listing and human-selected repair for ambiguous legacy SQLite
  outcome rows.
- Added deterministic bootstrap outcome-yield reporting with explicit
  no-positive/no-finite-estimate status for the current pilot.
- Pinned GitHub Actions by commit and restricted workflow permissions.
- **feat!**: Raised the default Stage 2 corpus gate to 800 test rows with at
  least 50 positive and 50 negative outcomes per family; small smoke tests
  must now override those floors explicitly.

## [0.2.0] - 2026-09-12

- Added Sigstore DSSE and Rekor inclusion verification before Stage 2 can emit
  replay-feasibility evidence.
- Made SQLite signal and outcome linkage include `strategy_version`, rejecting
  ambiguous legacy rows and reads.
- Replaced Python-specific identity serialization with RFC 8785 canonical JSON
  so hashes are independently reproducible across languages.
- Exposed calibration controls for evaluation diagnostics.
- Made the per-module coverage gate fail closed when a production module is
  absent from coverage data.
- Clarified the injected runner's synthetic scope and its production boundary.

## [0.1.0] - 2026-09-05

- Initial Isoprax v0.3 reference implementation release.
- Added Stage 1 admission and public-data evidence infrastructure.
- Added bounded Stage 2 replay-feasibility and corpus-evaluation reducers.
