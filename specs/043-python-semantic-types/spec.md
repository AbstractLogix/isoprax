# Feature Specification: Strongly Typed Python Semantic Core

**Feature Branch**: `codex/043-python-semantic-types`

**Created**: 2026-09-25

**Status**: Implemented locally; hosted CI pending

**Input**: User direction: make Python the strongly typed implementation of Isoprax semantics, applying type-system discipline to the Python codebase.

## User Scenarios & Testing

### User Story 1 - Construct validated semantic values (Priority: P1)

A maintainer receives structured outcome and evidence data and constructs validated semantic values before using comparison, calibration, admission, or conformance operations. The values expose normalized fields with precise types rather than retaining arbitrary strings, mappings, or untyped payloads as domain state.

**Why this priority**: Every later semantic guarantee depends on the domain model accurately representing validated values.

**Independent Test**: Type-check constructors and consumers for accepted inputs, reject malformed boundary inputs at runtime, and confirm that normalized values retain existing decisions.

**Acceptance Scenarios**:

1. **Given** a valid structured outcome input, **when** it is parsed, **then** the resulting value contains normalized outcome, observation-process, window, and threshold types.
2. **Given** malformed, incomplete, or unknown semantic fields in raw data, **when** it is parsed, **then** parsing fails explicitly and no validated semantic value is returned.
3. **Given** an existing supported Python input form, **when** it is parsed, **then** its comparison decision remains unchanged.

### User Story 2 - Require typed evidence for stronger decisions (Priority: P1)

A maintainer asks to pool or strengthen a claim and receives an operation whose input types express the required relationship and evidence. Direct, bridgeable, and irreducible comparisons remain distinguishable. Attestations retain provenance but cannot make mismatched definitions commensurable, and calibration does not upgrade structural conformance.

**Why this priority**: Type safety matters only where it protects semantic boundaries and claim eligibility.

**Independent Test**: Positive and expected-failure type-check examples exercise missing, mismatched, or insufficient evidence; runtime properties confirm evidence remains bound to its definitions.

**Acceptance Scenarios**:

1. **Given** no commensurability proof or calibration evidence, **when** a caller attempts pooled comparison, **then** static checking rejects the call.
2. **Given** evidence bound to different definitions or an attestation for mismatched definitions, **when** authorization is requested, **then** it is rejected and no pooled result is emitted.
3. **Given** calibration and commensurability evidence for a Stage 0 report, **when** conformance is evaluated, **then** the result remains Structural.

### User Story 3 - Enforce the typing contract in development (Priority: P1)

A contributor receives an automated failure when semantic code introduces an untyped or incompatible value flow, before the change is merged. Dynamic input boundaries remain checked at runtime.

**Why this priority**: Types provide no reliable guarantee if the project does not check them consistently.

**Independent Test**: Run the configured static check on the declared semantic scope and execute valid and invalid type examples in CI.

**Acceptance Scenarios**:

1. **Given** a clean semantic change, **when** the type check runs in its configured Python 3.10 target environment, **then** it completes without diagnostics or ignored errors in its declared scope. Runtime tests still run across the supported Python matrix.
2. **Given** an invalid evidence flow in a compile-time example, **when** the checker runs, **then** the example is rejected for the intended type error.
3. **Given** an untrusted structured input or non-integer calibration label, **when** it enters the typed model, **then** strict runtime validation occurs before it is represented as validated evidence.

### Edge Cases

- Optional and missing fields at parsing boundaries.
- Unknown keys, wrong JSON value types, and nested collections with mixed element types.
- Definition IDs or evidence endpoints that are blank, reversed, or unrelated.
- Calibration evidence used with another definition.
- Fractional or out-of-domain calibration labels at runtime boundaries.
- Valid legacy constructors and persisted payloads that currently accept strings or mappings.
- Python 3.10 syntax and standard-library typing differences through Python 3.14.
- Third-party numerical types at typed boundaries without weakening semantic core types to `Any`.

## Requirements

### Functional Requirements

- **FR-001**: The semantic core MUST distinguish raw external input from validated domain values.
- **FR-002**: Validated outcome fields MUST have precise normalized types; they MUST NOT retain unions of raw mappings and domain objects as stored state.
- **FR-003**: Comparison outcomes MUST be represented as a closed, typed set of direct, bridgeable, and irreducible results with typed differing fields. An attestation MAY be retained as provenance but MUST NOT alter the mechanical commensurability decision.
- **FR-004**: Typed pooled evaluation MUST require commensurability evidence and passing calibration evidence for both compared definitions. Runtime validation MUST bind calibration evidence to the concrete definition ID and exact normalized score/outcome sample; pooled evaluation MUST reject a different sample.
- **FR-005**: Calibration, admission, and conformance result types MUST preserve the existing Structural/Semantic/Full boundaries and MUST NOT silently upgrade claims.
- **FR-006**: The declared semantic Python scope MUST pass a strict static type check in local development and hosted CI without suppressions that hide errors in that scope.
- **FR-007**: Expected-failure typing examples MUST demonstrate that representative missing or mismatched evidence cannot be passed to typed operations.
- **FR-008**: Raw JSON, legacy flexible inputs, and direct semantic-value constructors MUST be validated at runtime. Required definition IDs, events, observation processes, and windows MUST be non-empty. Supported existing Python behavior and wire representations MUST remain stable unless a specification conflict is found and documented.
- **FR-009**: Property-based tests MUST cover normalization stability, deterministic identity, commensurability invariants, fail-closed behavior, and claim non-upgrade.
- **FR-010**: Python remains the sole maintained implementation of Isoprax semantic operations as well as the primary implementation for corpus processing, numerical work, ML/JEPA, and evaluation orchestration. This feature MUST remove the Haskell kernel, its CI workflow, benchmark, and active documentation while retaining the completed experiment record under `specs/042-haskell-semantics-kernel/`.
- **FR-011**: Definitions differing in event, observation process, window, or thresholds MUST remain non-commensurable and non-poolable regardless of free-text attestation or retained observations. Pooling may proceed only after an applied transformation re-derives outcomes under a shared definition and validates that definition.
- **FR-012**: Structured observation-process, window, and threshold mappings MUST reject unknown fields rather than silently dropping potentially semantic input.
- **FR-013**: Calibration outcomes MUST be exact binary integer labels at runtime. Validation and sample hashing MUST NOT coerce fractional or otherwise non-integer labels into integers.
- **FR-014**: Direct `Threshold` construction MUST enforce the same field-type, finiteness, and nonnegative-sustain invariants as mapping construction.

### Key Entities

- **Raw Semantic Input**: Untrusted structured data received from JSON, persistence, or a caller.
- **Validated Outcome Definition**: A normalized event, observation process, window, and threshold set used for semantic comparison.
- **Evidence Value**: Validated evidence bound to one or more outcome definitions.
- **Typed Decision**: A closed result that records direct equivalence, bridgeability, or irreducibility; any supplied attestation remains provenance metadata and cannot change the result.
- **Calibration Qualification**: The checked result for a definition-specific score/outcome sample.
- **Conformance Claim**: A Structural, Semantic, or Full result whose strength is limited by available evidence.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every file in the declared semantic typing scope passes the strict type check with zero errors and zero blanket ignores.
- **SC-002**: At least six expected-failure examples reject unsafe evidence use, while valid calls type-check.
- **SC-003**: Existing supported behavior and serialized decision shapes remain stable, except for documented fail-closed corrections where prior behavior conflicts with the authoritative Isoprax specification.
- **SC-004**: The property suite runs at least 1,000 generated cases for each core invariant and includes malformed and boundary inputs.
- **SC-005**: The strict typing job completes in under two minutes on the standard hosted Linux runner.
- **SC-006**: No production Python entry point depends on a second runtime to make semantic decisions.
- **SC-007**: A pooled evaluation rejects score/outcome samples whose canonical digest differs from the samples used to establish calibration evidence.
- **SC-008**: Empty required definition fields and unknown semantic mapping keys are rejected; retained observations and free-text attestations never make non-commensurable definitions poolable; calibration rejects non-integer binary labels without lossy coercion.
- **SC-009**: Direct `Threshold` construction rejects invalid field types, non-finite numeric values, and negative sustain values.

## Assumptions

- Python remains the primary language and will use its static checker, generic types, discriminated unions, and runtime validators where each adds a real guarantee.
- Public JSON and persisted shapes remain compatible unless the authoritative Isoprax specification requires a correction.
- The initial implementation focuses on the deterministic evidence and commensurability core; broad ML tensor typing is out of scope for this slice.
- The user has directed the project to commit to Python; the completed Haskell experiment remains documented as historical evidence, while its source and maintained CI surface are removed.
