# Feature Specification: Haskell Reference Semantics Kernel

**Feature Branch**: `codex/042-haskell-semantics-kernel`

**Created**: 2026-09-24

**Status**: Implemented; hosted CI and merge remain pending

**Input**: User description: evaluate and implement a narrow, independently testable Haskell kernel for Isoprax's deterministic evidence, commensurability, conformance, identity, and selected evaluation semantics.

## User Scenarios & Testing

### User Story 1 - Check outcome commensurability (Priority: P1)

A maintainer submits two structured Outcome Definitions and receives a deterministic decision explaining whether the outcomes are directly commensurable, attested equivalent, bridgeable, or irreducible. The decision states whether pooling is permitted and identifies every differing field.

**Why this priority**: Commensurability is the strongest candidate for an independent semantic reference. Opaque evidence values can make unsafe pooling harder to express while preserving the current Python decision rules.

**Independent Test**: Run valid pairs covering direct matches, threshold/window differences, explicit bridge records, matching and mismatched attestations, event changes, observation-process changes, and malformed definitions through both implementations. Compare the decision projection and confirm missing evidence never promotes the result.

**Acceptance Scenarios**:

1. **Given** structurally equal Outcome Definitions, **when** they are compared, **then** the result is direct and pooling is permitted.
2. **Given** only a window or threshold differs, **when** no attestation or complete bridge record is present, **then** the result is bridgeable and pooling is withheld.
3. **Given** an attestation names both definitions and has non-empty provenance and justification, **when** only bridgeable fields differ, **then** the result is attested and pooling is permitted.
4. **Given** a bridge record binds both definitions to a transformation identifier, retained-observation manifest, and provenance reference, **when** only window or threshold semantics differ, **then** the result remains bridgeable and the existing policy permits pooling.
5. **Given** event or observation-process semantics differ, **when** an attestation or bridge is supplied, **then** the result remains irreducible and pooling is withheld.
6. **Given** malformed or incomplete input, **when** the request is evaluated, **then** it fails closed with a stable error category and no successful evidence value.

### User Story 2 - Require explicit evidence for stronger decisions (Priority: P1)

A maintainer evaluates calibration, selected admission evidence, or a conformance claim. The kernel distinguishes validated evidence from raw input and does not silently upgrade Structural to Semantic or Full Conformance.

**Why this priority**: The kernel is useful only if its types make evidence requirements visible and its decisions preserve Isoprax's claim boundaries.

**Independent Test**: Exercise calibration fit/gate separation, anchored provenance and predeclaration, calibration qualification, and Structural/ Semantic claim decisions with present, missing, malformed, and contradictory evidence. Compile negative API examples showing that pooling cannot be called without permitted commensurability evidence and calibrated values.

**Acceptance Scenarios**:

1. **Given** calibration evidence with overlapping, unknown, or wrongly assigned row sets, **when** the selected admission rule runs, **then** that gate fails.
2. **Given** missing provenance, private/privileged provenance, missing external anchoring, or a predeclaration at or after collection start, **when** the selected admission rule runs, **then** that gate fails.
3. **Given** Stage 0 cross-family evidence, **when** calibration or commensurability succeeds, **then** the report remains Structural and never upgrades itself to Semantic or Full.
4. **Given** a caller requests an authorized pooled comparison, **when** either calibration or poolability evidence is absent, **then** the public Haskell operation cannot be called and no pooled result is emitted.

### User Story 3 - Verify canonical identity independently (Priority: P2)

A maintainer supplies an identity payload and receives the same canonical representation and SHA-256 identity as the Python implementation.

**Why this priority**: Cross-runtime canonical identity supports reproducible evidence, replay, attestations, and fixtures without moving Python's data and research work.

**Independent Test**: Compare canonical UTF-8 bytes and digest outputs for shared valid JSON fixtures, including key ordering, Unicode, arrays, finite numbers, and empty containers. Verify invalid JSON-domain values fail closed and that repeated/equivalent canonical inputs have stable identities.

**Acceptance Scenarios**:

1. **Given** equivalent JSON objects with different member insertion order, **when** identity is computed, **then** canonical bytes and digest match the Python reference exactly.
2. **Given** a number or string outside the supported canonical domain, **when** identity is requested, **then** the request fails explicitly instead of producing a different digest.
3. **Given** one canonical identity request is repeated, **when** the same payload is supplied, **then** the output is byte-for-byte identical.

### User Story 4 - Detect semantic drift and measure the CLI seam (Priority: P2)

A maintainer runs the shared fixture suite, property suite, and benchmark to determine whether the Haskell implementation provides independent correctness value and what latency the subprocess interface adds.

**Why this priority**: A second implementation is justified only when it exposes invalid states, improves invariant testing, or independently verifies normative behavior. Measured results inform whether it should remain.

**Independent Test**: Run every shared fixture through the Haskell CLI and Python oracle, execute the Haskell property suite, and record cold/warm CLI latency against the Python in-process reference with environment and sample counts.

**Acceptance Scenarios**:

1. **Given** a shared normative fixture, **when** both implementations run, **then** their normalized decisions and canonical identity output are identical or the test fails with the fixture and differing fields identified.
2. **Given** generated valid and malformed values, **when** properties run, **then** canonicalization stability, identity determinism, required symmetry/reflexivity, fail-closed incompatibility, and non-upgrading claim rules hold.
3. **Given** an API call that lacks required proof values, **when** a compile-fail example is checked, **then** the public Haskell interface rejects it at compile time.
4. **Given** the benchmark is run, **when** it completes, **then** it reports the subprocess overhead and Python comparison measurements without claiming a speedup from unmatched workloads.

## Edge Cases

- A request is empty, malformed, has an unsupported operation/version, or contains unknown required evidence fields.
- An Outcome Definition is missing an identifier, event, observation process, window, or well-formed threshold.
- Attestation endpoints are missing, reversed incorrectly, unrelated to the definitions, or have blank provenance/justification.
- A window/threshold mismatch is bridgeable, but the bridge record is missing, incomplete, or bound to different definitions.
- Event or observation-process mismatch is accompanied by otherwise valid calibration or attestation evidence.
- Calibration samples are empty, mismatched in length, have invalid scores/labels, contain one class, have constant scores, or fall below the declared support floor.
- Calibration fit/gate evidence is missing, overlaps, references unknown rows, or uses the wrong split.
- Provenance is absent, privately sourced, privileged, lacks an independent anchor, or was declared after data collection began.
- JSON contains non-finite or out-of-domain numbers, unsupported values, invalid UTF-8, or strings requiring canonical escaping.
- The Haskell executable is absent or exits unsuccessfully; the Python harness reports this as unavailable/failure and never treats it as a passing differential result.
- A Python/Haskell disagreement is detected; it is surfaced as a semantic review event and is not silently normalized away.

## Requirements

### Functional Requirements

- **FR-001**: The kernel MUST expose a deterministic, offline, line-oriented command interface that accepts one versioned JSON request and returns one JSON result without network access.
- **FR-002**: The kernel MUST validate raw Outcome Definitions and construct validated domain values only through smart constructors.
- **FR-003**: The commensurability evaluator MUST preserve Isoprax's direct, attested, bridgeable, and irreducible outcomes, differing-field list, reason category, and pooling decision. For a bridgeable mismatch, poolability MUST require an explicit record bound to both definition IDs and containing non-empty transformation, retained-observation-manifest, and provenance references. This records declared bridge evidence; it does not execute or independently validate the transformation.
- **FR-004**: The public pooling-authorization operation MUST require an opaque successful pooling-evidence value and two qualified calibration values. The relevant constructors MUST remain private to the Haskell library and invalid proof values MUST NOT be constructible through its public interface.
- **FR-005**: The Stage 0 conformance evaluator MUST match the Python report's Structural class and calibration qualifier. It MUST preserve the Structural/Semantic/Full distinction and MUST NOT upgrade Stage 0 to Semantic or Full from calibration, commensurability, or absent evidence.
- **FR-006**: The selected admission surface MUST cover only the existing calibration-fit/gate split separation and provenance/predeclaration gates. It MUST state that it does not replace the Python Stage 1 corpus-admission pipeline.
- **FR-007**: The kernel MUST implement the shared identity format using RFC 8785 canonical JSON and SHA-256, returning the canonical representation used for hashing as well as the digest.
- **FR-008**: The Python/Haskell differential suite MUST run shared fixtures for commensurability, selected admission gates, calibration/conformance decisions, malformed inputs, and canonical identity. It MUST call the existing Python semantic functions for supported behavior, use a documented normalized result projection, and fail on any disagreement.
- **FR-009**: The property suite MUST cover canonicalization/identity stability, applicable reflexivity and symmetry, fail-closed incompatible definitions, missing-evidence non-upgrade, and the rule that stronger claims cannot follow from weaker evidence alone.
- **FR-010**: The benchmark MUST compare equivalent commensurability and identity workloads, report cold and warm subprocess latency with sample counts and runtime versions, and record the Python comparison. It MUST describe process-startup cost as part of the selected CLI interface.
- **FR-011**: The architecture note MUST identify the semantics owned by the Haskell kernel and state that acquisition, corpus construction, ML/JEPA, NumPy/PyTorch evaluation, experimentation, visualization, notebooks, and orchestration remain Python-owned.
- **FR-012**: The implementation MUST add no Haskell service, FFI, network protocol, or Haskell dependency to Python's base runtime.
- **FR-013**: The final assessment MUST identify compile-time invalid states that the interface prevents, differential/property evidence obtained, benchmark results, and any semantic limits. If no material correctness benefit is demonstrated, it MUST recommend removing the kernel.

### Key Entities

- **Raw Outcome Definition**: Untrusted structured event, observation process, window, and threshold input.
- **Validated Outcome Definition**: A domain value that passed structural and semantic validation.
- **Attestation**: Named, provenance-backed evidence relating two specific definitions.
- **Commensurability Evidence**: A decision value recording the relationship and whether pooling is permitted.
- **Calibration Evidence**: Declared score/outcome support and the resulting calibration qualification.
- **Admission Evidence**: The selected calibration split and provenance/predeclaration gate inputs and results.
- **Conformance Decision**: A bounded Structural/Semantic/Full result with explicit evidence requirements and no implicit upgrade.
- **Canonical Identity**: RFC 8785 UTF-8 representation and SHA-256 digest of an eligible JSON payload.
- **Differential Fixture**: A shared request and expected normalized decision accepted by both runtimes.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every shared fixture in the four evidence categories—commensurability, selected admission, conformance/evaluation, and canonical identity—produces an identical normalized result in Python and Haskell.
- **SC-002**: The property suite passes at least 1,000 generated cases per configured property, including malformed/boundary generators, with any counterexample reported reproducibly.
- **SC-003**: Pooling authorization requires both opaque commensurability and calibration evidence; compile-fail checks reject calls that omit either.
- **SC-004**: Canonical representation bytes and SHA-256 match Python RFC 8785 fixtures exactly, including Unicode and numeric boundary cases in the shared supported domain.
- **SC-005**: A clean checkout can build the kernel, run its properties, and run the Python differential suite using documented commands and pinned dependency resolution.
- **SC-006**: The benchmark records cold and warm p50/p95 latency for at least 100 CLI invocations and the corresponding Python in-process workload, with toolchain and host details.
- **SC-007**: The architecture note and convergence record state whether stronger types and independent differential checks materially improved correctness, with evidence for that conclusion.

## Assumptions

- Python remains the primary implementation and source for data acquisition, corpus construction, model training, numerical analysis, experimentation, visualization, notebooks, and orchestration.
- The kernel is a separate offline executable that consumes structured JSON; no FFI or service deployment is required.
- The shared admission surface covers two existing pure Python gates only. Full Stage 1 corpus assembly/admission and Stage 2 evaluation remain Python-owned.
- The bridge record makes retained-observation evidence explicit at the kernel boundary; the Python adapter validates the record and maps its presence to the existing `retained_observations` input. This preserves current decisions without claiming that the kernel verified a transformation's correctness.
- Python's existing functions are the oracle for supported shared decisions. The versioned kernel request is stricter than legacy loose inputs where necessary; this wire-profile validation is documented and tested separately from the normalized decision projection.
- Benchmark timing is descriptive. The subprocess design is retained only if its type-safety or independent-verification benefits are demonstrated.
- Haskell toolchain setup and package versions will be chosen during planning and pinned for reproducible builds.
