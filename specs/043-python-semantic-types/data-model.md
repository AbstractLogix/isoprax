# Data Model: Strongly Typed Python Semantic Core

## Raw outcome input

An untrusted constructor/parser input consisting of an identifier, event, observation process, window, thresholds, and description. Observation process, window, and thresholds may use documented legacy strings or mappings. The parser accepts `object` at its external boundary, validates shape and values, rejects unknown mapping fields, and returns no domain value on malformed input.

## Normalized outcome definition

An immutable semantic value containing:

- `id: str`
- `event: str` in normalized form
- `observation_process: ObservationProcess`
- `window: Window`
- `thresholds: tuple[Threshold, ...]`
- `description: str`

Construction preserves supported legacy inputs, but stored fields contain only normalized types. Canonical comparison continues to ignore identity and description and compares event, observation process, window, and thresholds. `definition_content_digest` is the canonical digest of that normalized comparison key; it excludes the separate definition ID and non-semantic description.

## Calibration policy

An immutable policy with `min_events`, `n_bins`, and `max_ece`. It validates its supported value ranges and exposes a canonical digest. Both sides of one typed pooled authorization must carry equal policy values.

## Threshold

An immutable value that validates its own metric, operator, numeric value, sustain, unit, and raw-description fields. Direct construction and mapping parsing enforce the same type, finite-number, and nonnegative-sustain constraints.

## Commensurability result

A closed discriminated union for direct, bridgeable-without-retained-observations, bridgeable-with-retained-observations, and irreducible results. Each variant carries typed differing fields, IDs, reason, and optional attestation. An attestation records provenance but cannot override the mechanical test. Definitions that differ in event, process, window, or thresholds remain non-commensurable and non-poolable until outcomes are actually re-derived under a shared definition.

## Calibration evidence

A generic evidence value parameterized by a caller-defined marker type. It contains the concrete definition ID, normalized definition-content digest, passing calibration summary, exact normalized score/outcome sample digest, and the policy used for qualification. A factory rejects failed calibration results, requires exact binary integer outcomes without lossy coercion, and binds evidence to the definition, sample, and policy.

## Commensurability evidence

A generic evidence value parameterized by the left and right outcome marker types. It contains the concrete IDs, the normalized content digest for each definition, and a successful pooling-eligibility result. Its factory calls the existing deterministic commensurability policy and rejects results whose pooling is not allowed.

## Pooled-comparison authorization

A generic value produced only when the relation and both calibration evidence objects have compatible marker parameters. The constructor checks concrete left/right IDs and definition-content digests, requires both calibrations to use the same policy, and carries both sample digests and the policy. Pooled evaluation rejects different score/outcome vectors and uses the authorized policy's bin count.

## CI-only semantic oracle

An independent Haskell implementation of the direct commensurability and typed pooled-evidence boundary. It derives the same normalized definition, sample, and policy digests from shared fixtures, issues opaque evidence only after validation, and evaluates pooled ECE with the bound policy. It is a CI reference only and is never called by Python runtime code.

## Stage 0 conformance

The existing cross-family report remains Structural. Its pooled ECE is a same-call diagnostic for directly commensurable definitions, including uncalibrated ones; it is not typed pooled authorization. Neither successful calibration nor successful pooling authorization changes the report's conformance class. This data model does not add Semantic or Full claim constructors.

## Admission discriminants

Corpus split names, row outcome classes, admission gate IDs, and the fixed "admission evidence only" claim boundary use closed literal types. Runtime constructors continue to validate untrusted values before accepting them.
