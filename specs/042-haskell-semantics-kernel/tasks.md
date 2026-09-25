# Tasks: Haskell Reference Semantics Kernel

**Input**: Design documents from /specs/042-haskell-semantics-kernel/

**Prerequisites**: spec.md, plan.md, research.md, data-model.md, contracts/kernel-cli-v1.md

**Tests**: Property, differential, and compile-fail checks are required by the feature specification.

## Phase 1: Setup

**Purpose**: Establish reproducible Haskell package and compiler metadata.

- [X] T001 Create the isolated Cabal library/executable at haskell/isoprax-kernel/, pin compiler/package resolution, and add focused build commands.
- [X] T002 Add a Linux CI workflow for Haskell build, QuickCheck, compile-fail checks, and Python differential tests.

## Phase 2: Foundational protocol and typed domain

**Purpose**: Define the stable JSON boundary and hide invalid-state constructors before operations are added.

- [X] T003 Define the versioned JSON Lines protocol, duplicate-key-aware parsing, canonical response encoding, and categorized errors in haskell/isoprax-kernel/src/Isoprax/Kernel/Protocol.hs and app/Main.hs.
- [X] T004 Define opaque validated OutcomeDefinition, AttestationEvidence, BridgeEvidence, PoolingEvidence, and KernelError values in haskell/isoprax-kernel/src/Isoprax/Kernel.hs and focused modules.

## Phase 3: User Story 1 — Commensurability

**Purpose**: Independently evaluate current Isoprax outcome comparison and explicit evidence requirements.

- [X] T005 Add direct, attested, bridgeable, irreducible, malformed, and threshold-order fixture cases under tests/reference/commensurable/, bridgeable/, non_commensurable/, and malformed/.
- [X] T006 Implement normalized comparison, endpoint-bound attestation/bridge validation, stable decision projection, and QuickCheck properties in haskell/isoprax-kernel/src/Isoprax/Kernel/Commensurability.hs and test/Spec.hs.
- [X] T007 Add compile-fail examples proving that pooling authorization cannot be called without opaque PoolingEvidence and two qualified calibration values.

## Phase 4: User Story 2 — Calibration, selected admission, and Stage 0 conformance

**Purpose**: Preserve the selected evidence gates and current Stage 0 claim ceiling.

- [X] T008 Add calibration, admission, and conformance fixtures for valid, boundary, missing, overlapping, wrongly assigned, private, unanchored, and late-predeclaration evidence under tests/reference/.
- [X] T009 Implement calibration qualification and equal-width ECE decision rules in haskell/isoprax-kernel/src/Isoprax/Kernel/Calibration.hs; keep qualified evidence opaque.
- [X] T010 Implement only fit/gate split separation and provenance/predeclaration rules in haskell/isoprax-kernel/src/Isoprax/Kernel/Admission.hs.
- [X] T011 Implement Stage 0 cross-family projection in haskell/isoprax-kernel/src/Isoprax/Kernel/Conformance.hs; verify calibration or commensurability never upgrades it to Semantic or Full.

## Phase 5: User Story 3 — Canonical identity

**Purpose**: Produce byte-identical canonical JSON and content identity.

- [X] T012 Add RFC, Unicode, duplicate-key, safe-integer, negative-zero, exponent, and 1e23 fixtures under tests/reference/identity/.
- [X] T013 Implement RFC 8785 canonicalization and SHA-256 in haskell/isoprax-kernel/src/Isoprax/Kernel/Identity.hs; compare exact bytes with Python and fail the task if the selected encoder diverges.
- [X] T014 Add QuickCheck properties for canonical identity stability and equivalent object key order.

## Phase 6: User Story 4 — Differential verification, benchmark, and decision record

**Purpose**: Measure independence, correctness, and the subprocess boundary.

- [X] T015 Add tests/test_haskell_differential.py and its Python oracle adapter using existing Isoprax functions; compare every shared fixture by the contract's normalized projection.
- [X] T016 Add scripts/benchmark_haskell_kernel.py to report one first invocation and at least 100 warm invocations, Python in-process latency, p50/p95, and tool/runtime metadata.
- [X] T017 Write docs/haskell-reference-kernel.md and specs/042-haskell-semantics-kernel/assessment.md with architecture boundary, compile-time benefit, fixture/property results, benchmark, semantic limits, and keep/remove recommendation.
- [X] T018 Run focused Python tests, full Haskell property suite, compile-fail checks, differential fixtures, benchmark, and document only evidence actually obtained in specs/042-haskell-semantics-kernel/converge.md.
