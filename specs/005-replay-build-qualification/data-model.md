# Data Model: Hermetic Replay Build Qualification

## BuildSample

- Ordered unique commit identifiers.
- Frozen build recipe reference.
- One `LegalCoverageRecord` per commit.
- One `RunnerDescriptor`.
- Content-addressed preparation hash.

## BuildRowResult

- Commit identifier and terminal status: `success`, `censored`, or `blocked-before-compilation`.
- Stable diagnostic reason and optional runner evidence.

## BuildQualificationReport

- Preparation hash and all ordered row results.
- `measured_success_rate` only for a complete execution.
- Frozen floor, clustering outcome, qualification disposition, and `claim_scope=build_qualification_only`.
