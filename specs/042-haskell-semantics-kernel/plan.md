# Implementation Plan: Haskell Reference Semantics Kernel

**Branch**: codex/042-haskell-semantics-kernel | **Date**: 2026-09-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from /specs/042-haskell-semantics-kernel/spec.md

## Summary

Build an isolated Haskell library and line-oriented CLI under haskell/isoprax-kernel/. It will validate structured requests, independently evaluate the current commensurability and calibration rules, expose only the two requested pure admission gates, preserve the Stage 0 Structural claim boundary, and produce RFC 8785 canonical JSON plus SHA-256. Opaque Haskell evidence values will gate pooled-comparison authorization. Python remains the data and research runtime; the Python differential adapter calls the repository's existing semantic functions.

Bridgeable window/threshold pairs retain the existing policy result, but the kernel wire contract requires a complete bridge record bound to both definition IDs. The adapter validates that record and passes the existing Python retained-observations input. This records declared bridge evidence; it does not prove the transformation was run correctly.

## Technical Context

**Language/Version**: GHC2024 with GHC 9.14.1; Cabal 3.16.1.0. Python differential harness uses the repository's supported uv environment.

**Primary Dependencies**: aeson 2.2.5.1 for JSON values and RFC 8785 output, attoparsec-aeson 2.2.2.0 plus attoparsec for duplicate-key-aware parsing, cryptohash-sha256 for content identity, and QuickCheck 2.18.0.0 for properties. Exact resolved package versions are frozen in Cabal metadata.

**Storage**: N/A; local JSON fixtures and CLI streams only.

**Testing**: cabal test, Haskell QuickCheck properties (minimum 1,000 cases each), compile-fail API checks, and uv run pytest tests/test_haskell_differential.py.

**Target Platform**: Offline Linux CLI; pure library design with no OS service dependencies.

**Project Type**: Standalone Haskell library and executable, with Python test/benchmark adapters.

**Performance Goals**: Measure first-process and at least 100 subsequent subprocess invocations against comparable Python in-process checks; no latency target because process startup is part of the reference boundary.

**Constraints**: No network service, FFI, Haskell dependency in Python base runtime, or migration of acquisition, corpora, ML/JEPA, numerical research, notebooks, or orchestration. CLI emits one canonical JSON response per input line and stable categorized errors.

**Scale/Scope**: Structured evidence objects and selected evaluation arrays; no corpus ingestion or model-training workloads.

## Constitution Check

- **I. Specification Authority — PASS**: Implement only published v0.3 semantics for Outcome Definition comparison, calibration, and Stage 0 reporting; bridgeability remains distinct from semantic commensurability.
- **II. Honest Conformance — PASS**: Stage 0 remains Structural, even when calibration passes or outcomes are commensurable. No synthetic evidence is described as efficacy or Semantic/Full conformance.
- **III. Contract-First Testing — PASS**: Each supported operation has malformed and boundary fixtures, generated properties, and Python comparison projections.
- **IV. Deterministic Core, Explicit Effects — PASS**: Domain decisions are pure. JSON lines and SHA-256 are the only boundary effects; no network access.
- **V. Minimal Reference Scope — PASS WITH EXPLICIT USER SCOPE**: The user specifically requested selected admission and evaluation rules. Implement only calibration fit/gate separation and provenance/predeclaration checks; do not port the complete Stage 1 gate or Stage 2 pipeline.

## Design Decisions

1. Keep a versioned request schema and one operation per JSON line: commensurability, calibration, admission, conformance, or identity.
2. Hide constructors for validated outcomes, bridge/attestation proofs, calibration qualification, and pooling evidence. Public functions validate raw values and return Either KernelError.
3. Keep pooling authorization separate from metric calculation. It requires a poolability proof plus two calibrated evidence values; report generation continues in Python.
4. Compare normalized semantic fields: event and observation-process identity, window semantics, and thresholds as an unordered set. IDs and descriptions do not affect equality. Return stable reason codes and sorted differing-field names.
5. Make bridge evidence an explicit, endpoint-bound descriptor. Do not claim that this kernel applies or verifies the recorded transform.
6. Preserve Python Stage 0 reporting exactly: cross-family reports remain Structural with the same calibration qualifier and bridgeable-pooling label.
7. Treat RFC 8785 compliance as a release gate. Run RFC vectors, Python rfc8785 fixtures, duplicate-key rejection, Unicode, and binary64 edge cases against the exact frozen Haskell encoder. If it disagrees, fix or replace the encoder; do not weaken fixtures or claim RFC compliance.
8. Benchmark equivalent decision and identity payloads. Report process startup separately from in-process Python time.

## Project Structure

### Documentation (this feature)

~~~text
specs/042-haskell-semantics-kernel/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/kernel-cli-v1.md
├── quickstart.md
├── tasks.md
├── assessment.md
└── converge.md
~~~

### Source Code (repository root)

~~~text
haskell/isoprax-kernel/
├── app/Main.hs
├── src/Isoprax/Kernel.hs
├── src/Isoprax/Kernel/
│   ├── Admission.hs
│   ├── Calibration.hs
│   ├── Commensurability.hs
│   ├── Conformance.hs
│   ├── Identity.hs
│   └── Protocol.hs
├── test/Spec.hs
├── test/CompileFail/
├── cabal.project
├── cabal.project.freeze
└── isoprax-kernel.cabal

tests/reference/
├── commensurable/
├── non_commensurable/
├── bridgeable/
├── malformed/
├── missing_evidence/
├── calibration/
├── admission/
├── conformance/
└── identity/

tests/test_haskell_differential.py
scripts/benchmark_haskell_kernel.py
docs/haskell-reference-kernel.md
~~~

**Structure Decision**: Keep Haskell isolated below haskell/, with only the Python differential runner and benchmark in existing Python tooling. No production Python module calls the subprocess.

## Complexity Tracking

No constitution violation. Selected admission checks are limited to the user-requested existing pure gates; the full admission pipeline remains outside the kernel.
