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

Construction preserves supported legacy inputs, but stored fields contain only normalized types. Canonical comparison continues to ignore identity and description and compares event, observation process, window, and thresholds.

## Threshold

An immutable value that validates its own metric, operator, numeric value, sustain, unit, and raw-description fields. Direct construction and mapping parsing enforce the same type, finite-number, and nonnegative-sustain constraints.

## Commensurability result

A closed discriminated union for direct, bridgeable-without-retained-observations, bridgeable-with-retained-observations, and irreducible results. Each variant carries typed differing fields, IDs, reason, and optional attestation. An attestation records provenance but cannot override the mechanical test. Definitions that differ in event, process, window, or thresholds remain non-commensurable and non-poolable until outcomes are actually re-derived under a shared definition.

## Calibration evidence

A generic evidence value parameterized by a caller-defined marker type. It contains the concrete definition ID, passing calibration summary, and canonical digest of the exact normalized score/outcome sample. A factory rejects failed calibration results, requires exact binary integer outcomes without lossy coercion, and binds evidence to the definition and sample.

## Commensurability evidence

A generic evidence value parameterized by the left and right outcome marker types. It contains the concrete IDs and successful pooling-eligibility result. Its factory calls the existing deterministic commensurability policy and rejects results whose pooling is not allowed.

## Pooled-comparison authorization

A generic value produced only when the relation and both calibration evidence objects have compatible marker parameters. The constructor checks concrete left/right IDs and carries each calibrated sample digest; pooled evaluation rejects different score/outcome vectors.

## Stage 0 conformance

The existing cross-family report remains Structural. Neither successful calibration nor successful pooling authorization changes the report's conformance class. This data model does not add Semantic or Full claim constructors.

## Admission discriminants

Corpus split names, row outcome classes, admission gate IDs, and the fixed "admission evidence only" claim boundary use closed literal types. Runtime constructors continue to validate untrusted values before accepting them.
